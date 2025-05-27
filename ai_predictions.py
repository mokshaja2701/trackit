import pandas as pd
import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from datetime import datetime
import pytz
import logging

from app import db
from models import OrderHistory, User

# Indian Standard Time
IST = pytz.timezone('Asia/Kolkata')

class OrderPredictor:
    def __init__(self):
        self.window_time_encoder = LabelEncoder()
        self.delivery_speed_encoder = LabelEncoder()
        self.day_encoder = LabelEncoder()
        self.vendor_encoder = LabelEncoder()
        self.model_window = None
        self.model_speed = None
        self.is_trained = False
    
    def prepare_features(self, customer_id):
        """Prepare features for prediction"""
        try:
            # Get customer's order history
            history = OrderHistory.query.filter_by(customer_id=customer_id, was_successful=True).all()
            
            if len(history) < 5:
                return None
            
            # Convert to DataFrame
            data = []
            for record in history:
                data.append({
                    'customer_id': record.customer_id,
                    'vendor_id': record.vendor_id,
                    'window_time': record.window_time,
                    'delivery_speed': record.delivery_speed,
                    'order_day': record.order_day,
                    'order_hour': record.order_hour
                })
            
            df = pd.DataFrame(data)
            
            # Get current time features
            now = datetime.now(IST)
            current_day = now.strftime('%A').lower()
            current_hour = now.hour
            
            # Encode categorical variables
            df_encoded = df.copy()
            df_encoded['window_time_encoded'] = self.window_time_encoder.fit_transform(df['window_time'])
            df_encoded['delivery_speed_encoded'] = self.delivery_speed_encoder.fit_transform(df['delivery_speed'])
            df_encoded['day_encoded'] = self.day_encoder.fit_transform(df['order_day'])
            df_encoded['vendor_encoded'] = self.vendor_encoder.fit_transform(df['vendor_id'].astype(str))
            
            # Prepare feature matrix
            features = ['vendor_encoded', 'day_encoded', 'order_hour']
            X = df_encoded[features].values
            
            # Target variables
            y_window = df_encoded['window_time_encoded'].values
            y_speed = df_encoded['delivery_speed_encoded'].values
            
            return X, y_window, y_speed, current_day, current_hour
            
        except Exception as e:
            logging.error(f"Error preparing features: {str(e)}")
            return None
    
    def train_models(self, customer_id):
        """Train SVM models for window time and delivery speed prediction"""
        try:
            data = self.prepare_features(customer_id)
            if data is None:
                return False
            
            X, y_window, y_speed, _, _ = data
            
            if len(X) < 5:
                return False
            
            # Train SVM models
            self.model_window = SVC(kernel='rbf', probability=True, random_state=42)
            self.model_speed = SVC(kernel='rbf', probability=True, random_state=42)
            
            # If we have enough data, split for validation
            if len(X) > 10:
                X_train, X_test, y_window_train, y_window_test = train_test_split(
                    X, y_window, test_size=0.2, random_state=42
                )
                _, _, y_speed_train, y_speed_test = train_test_split(
                    X, y_speed, test_size=0.2, random_state=42
                )
                
                self.model_window.fit(X_train, y_window_train)
                self.model_speed.fit(X_train, y_speed_train)
            else:
                self.model_window.fit(X, y_window)
                self.model_speed.fit(X, y_speed)
            
            self.is_trained = True
            return True
            
        except Exception as e:
            logging.error(f"Error training models: {str(e)}")
            return False
    
    def predict(self, customer_id, vendor_id):
        """Make predictions for window time and delivery speed"""
        try:
            if not self.is_trained:
                if not self.train_models(customer_id):
                    return None
            
            # Get current time features
            now = datetime.now(IST)
            current_day = now.strftime('%A').lower()
            current_hour = now.hour
            
            # Encode current features
            try:
                day_encoded = self.day_encoder.transform([current_day])[0]
            except ValueError:
                # If day not seen before, use most common day
                day_encoded = 0
            
            try:
                vendor_encoded = self.vendor_encoder.transform([str(vendor_id)])[0]
            except ValueError:
                # If vendor not seen before, use most common vendor
                vendor_encoded = 0
            
            # Prepare feature vector
            features = np.array([[vendor_encoded, day_encoded, current_hour]])
            
            # Make predictions
            window_pred = self.model_window.predict(features)[0]
            speed_pred = self.model_speed.predict(features)[0]
            
            # Get prediction probabilities
            window_proba = self.model_window.predict_proba(features)[0]
            speed_proba = self.model_speed.predict_proba(features)[0]
            
            # Decode predictions
            window_time = self.window_time_encoder.inverse_transform([window_pred])[0]
            delivery_speed = self.delivery_speed_encoder.inverse_transform([speed_pred])[0]
            
            # Get confidence scores
            window_confidence = float(np.max(window_proba))
            speed_confidence = float(np.max(speed_proba))
            
            return {
                'window_time': window_time,
                'delivery_speed': delivery_speed,
                'window_confidence': window_confidence,
                'speed_confidence': speed_confidence
            }
            
        except Exception as e:
            logging.error(f"Error making predictions: {str(e)}")
            return None

# Global predictor instance
predictor = OrderPredictor()

def get_ai_predictions(customer_id, vendor_id=None):
    """Get AI predictions for a customer"""
    try:
        user = User.query.get(customer_id)
        if not user or not user.can_use_ai_predictions():
            return None
        
        # If no vendor specified, use the most common vendor from history
        if vendor_id is None:
            history = OrderHistory.query.filter_by(customer_id=customer_id).all()
            if not history:
                return None
            
            # Get most frequent vendor
            vendor_counts = {}
            for record in history:
                vendor_counts[record.vendor_id] = vendor_counts.get(record.vendor_id, 0) + 1
            
            vendor_id = max(vendor_counts, key=vendor_counts.get)
        
        predictions = predictor.predict(customer_id, vendor_id)
        
        if predictions:
            # Add user-friendly descriptions
            window_descriptions = {
                '30min': '30 मिनट में (30 minutes)',
                '1hour': '1 घंटे में (1 hour)',
                '2hour': '2 घंटे में (2 hours)',
                'flexible': 'लचीला समय (Flexible timing)'
            }
            
            speed_descriptions = {
                'express': 'तेज़ डिलीवरी (Express)',
                'standard': 'सामान्य डिलीवरी (Standard)',
                'economy': 'मितव्यी डिलीवरी (Economy)'
            }
            
            predictions['window_description'] = window_descriptions.get(
                predictions['window_time'], predictions['window_time']
            )
            predictions['speed_description'] = speed_descriptions.get(
                predictions['delivery_speed'], predictions['delivery_speed']
            )
            
            # Convert confidence to percentage
            predictions['window_confidence_percent'] = int(predictions['window_confidence'] * 100)
            predictions['speed_confidence_percent'] = int(predictions['speed_confidence'] * 100)
        
        return predictions
        
    except Exception as e:
        logging.error(f"Error getting AI predictions: {str(e)}")
        return None

def update_order_history(order):
    """Update order history for AI training"""
    try:
        now = datetime.now(IST)
        
        # Create order history record
        history = OrderHistory(
            customer_id=order.customer_id,
            vendor_id=order.vendor_id,
            window_time=order.window_time,
            delivery_speed=order.delivery_speed,
            order_day=order.created_at.strftime('%A').lower(),
            order_hour=order.created_at.hour,
            was_successful=(order.status == 'delivered')
        )
        
        db.session.add(history)
        
        # Update customer's successful order count if delivered
        if order.status == 'delivered':
            customer = User.query.get(order.customer_id)
            customer.successful_orders += 1
        
        db.session.commit()
        
        # Reset predictor to retrain with new data
        global predictor
        predictor.is_trained = False
        
        logging.info(f"Updated order history for order {order.id}")
        
    except Exception as e:
        logging.error(f"Error updating order history: {str(e)}")
