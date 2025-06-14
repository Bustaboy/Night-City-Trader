# ml/rl_trainer.py
"""
Arasaka RL Training Core - Deep Q-Network for adaptive trading strategies
"""
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from collections import deque
import random
import os

from config.settings import settings
from utils.logger import logger

class RLTrainer:
    def __init__(self):
        # Model parameters
        self.state_size = len(settings.ML["features"])
        self.action_size = 3  # Buy, Sell, Hold
        self.model_path = settings.RL["model_path"]
        
        # Training parameters
        self.gamma = settings.RL["gamma"]
        self.epsilon = settings.RL["epsilon"]
        self.epsilon_min = 0.01
        self.epsilon_decay = settings.RL["epsilon_decay"]
        self.learning_rate = settings.RL["learning_rate"]
        self.batch_size = settings.RL["batch_size"]
        
        # Memory for experience replay
        self.memory = deque(maxlen=2000)
        
        # GPU configuration
        self.gpu_available = len(tf.config.list_physical_devices('GPU')) > 0
        logger.info(f"GPU available for RL: {self.gpu_available}")
        
        # Scale batch size for GPU
        if self.gpu_available:
            self.batch_size *= 4
        
        # Initialize models
        self.model = self._load_or_create_model()
        self.target_model = self._load_or_create_model()
        self.update_target_model()
    
    def _load_or_create_model(self):
        """Load existing model or create new one"""
        try:
            if os.path.exists(self.model_path):
                model = load_model(self.model_path)
                logger.info("RL model loaded from disk")
                return model
        except Exception as e:
            logger.error(f"Model load failed: {e}")
        
        return self.build_model()
    
    def build_model(self):
        """Build the DQN model"""
        model = Sequential([
            Dense(128, input_dim=self.state_size, activation="relu"),
            Dropout(0.2),
            Dense(64, activation="relu"),
            Dropout(0.2),
            Dense(32, activation="relu"),
            Dense(self.action_size, activation="linear")
        ])
        
        model.compile(
            loss="mse",
            optimizer=Adam(learning_rate=self.learning_rate)
        )
        
        return model
    
    def update_target_model(self):
        """Copy weights from main model to target model"""
        self.target_model.set_weights(self.model.get_weights())
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay buffer"""
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state):
        """Choose action using epsilon-greedy policy"""
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        
        # Reshape state for prediction
        state = np.array(state).reshape(1, -1)
        
        # Use GPU if available
        with tf.device('/GPU:0' if self.gpu_available else '/CPU:0'):
            act_values = self.model.predict(state, verbose=0)
        
        return np.argmax(act_values[0])
    
    def replay(self):
        """Train model on batch of experiences"""
        if len(self.memory) < self.batch_size:
            return
        
        # Sample batch from memory
        minibatch = random.sample(self.memory, self.batch_size)
        
        # Prepare batch data
        states = np.array([experience[0] for experience in minibatch])
        actions = np.array([experience[1] for experience in minibatch])
        rewards = np.array([experience[2] for experience in minibatch])
        next_states = np.array([experience[3] for experience in minibatch])
        dones = np.array([experience[4] for experience in minibatch])
        
        # Use GPU if available
        with tf.device('/GPU:0' if self.gpu_available else '/CPU:0'):
            # Predict Q-values for starting states
            current_q_values = self.model.predict(states, verbose=0)
            
            # Predict Q-values for next states
            next_q_values = self.target_model.predict(next_states, verbose=0)
        
        # Update Q-values with Bellman equation
        for i in range(self.batch_size):
            if dones[i]:
                current_q_values[i][actions[i]] = rewards[i]
            else:
                current_q_values[i][actions[i]] = rewards[i] + self.gamma * np.max(next_q_values[i])
        
        # Train model
        with tf.device('/GPU:0' if self.gpu_available else '/CPU:0'):
            self.model.fit(states, current_q_values, epochs=1, verbose=0, batch_size=self.batch_size)
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def calculate_indicators(self, df):
        """Calculate technical indicators for RL features"""
        try:
            # Simple Moving Averages
            df["sma_20"] = df["close"].rolling(window=20, min_periods=1).mean()
            df["sma_50"] = df["close"].rolling(window=50, min_periods=1).mean()
            
            # RSI
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14, min_periods=1).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14, min_periods=1).mean()
            rs = gain / (loss + 1e-10)
            df["rsi_14"] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df["std_20"] = df["close"].rolling(window=20, min_periods=1).std()
            df["bollinger_upper"] = df["sma_20"] + 2 * df["std_20"]
            df["bollinger_lower"] = df["sma_20"] - 2 * df["std_20"]
            
            # MACD
            ema12 = df["close"].ewm(span=12, adjust=False, min_periods=1).mean()
            ema26 = df["close"].ewm(span=26, adjust=False, min_periods=1).mean()
            df["macd"] = ema12 - ema26
            
            # Additional features
            df["sentiment_score"] = 0.0
            df["whale_ratio"] = 0.0
            
            # Fill NaN values
            df = df.fillna(method='ffill').fillna(0)
            
            return df
            
        except Exception as e:
            logger.error(f"RL indicator calculation flatlined: {e}")
            return df
    
    def calculate_reward(self, price_data, action, fee_rate=0.001):
        """Calculate reward for an action"""
        try:
            price_change = (price_data["close"] - price_data["open"]) / price_data["open"]
            
            if action == 0:  # Buy
                return price_change - fee_rate
            elif action == 1:  # Sell
                return -price_change - fee_rate
            else:  # Hold
                return 0
                
        except Exception as e:
            logger.error(f"Reward calculation flatlined: {e}")
            return 0
    
    async def train(self, data):
        """Train the RL model"""
        try:
            logger.info("Starting RL model training...")
            
            # Convert to DataFrame
            df = pd.DataFrame(
                data,
                columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            # Extract features
            states = df[settings.ML["features"]].values
            
            # Check if we have enough data
            if len(states) < 10:
                raise ValueError("Insufficient data for RL training")
            
            # Training loop
            episodes = min(settings.RL["episodes"], 100)  # Cap episodes for performance
            
            for episode in range(episodes):
                # Reset for new episode
                total_reward = 0
                done = False
                
                # Train on sequences
                sequence_length = min(len(states) - 1, 1000)  # Limit sequence length
                
                for t in range(sequence_length):
                    # Get current state
                    current_state = states[t]
                    
                    # Choose action
                    action = self.act(current_state)
                    
                    # Get next state
                    next_state = states[t + 1] if t < len(states) - 1 else states[t]
                    
                    # Calculate reward
                    reward = self.calculate_reward(df.iloc[t], action)
                    total_reward += reward
                    
                    # Check if done
                    done = t == sequence_length - 1
                    
                    # Store experience
                    self.remember(current_state, action, reward, next_state, done)
                    
                    # Train on experience replay
                    if len(self.memory) > self.batch_size:
                        self.replay()
                
                # Update target model periodically
                if episode % 10 == 0:
                    self.update_target_model()
                    logger.info(f"RL Episode {episode}/{episodes} - Total Reward: {total_reward:.4f}, Epsilon: {self.epsilon:.3f}")
            
            # Save model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.model.save(self.model_path)
            logger.info(f"RL model saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"RL training flatlined: {e}")
            raise
    
    def predict(self, data):
        """Make prediction on new data"""
        try:
            # Prepare single data point
            if isinstance(data, (list, tuple)):
                df = pd.DataFrame(
                    [data],
                    columns=["timestamp", "open", "high", "low", "close", "volume"]
                )
            else:
                df = pd.DataFrame([data])
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            # Extract features
            state = df[settings.ML["features"]].values[0]
            
            # Get action
            action = self.act(state)
            
            # Convert to continuous value (0-1)
            # 0 = Buy (0.0), 1 = Sell (1.0), 2 = Hold (0.5)
            action_map = {0: 0.0, 1: 1.0, 2: 0.5}
            
            return action_map.get(action, 0.5)
            
        except Exception as e:
            logger.error(f"RL prediction flatlined: {e}")
            return 0.5  # Return neutral on error

# Create singleton instance
rl_trainer = RLTrainer()
