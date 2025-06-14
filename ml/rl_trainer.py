# ml/rl_trainer.py
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from collections import deque
import random
from config.settings import settings
from market.data_fetcher import fetcher
from utils.logger import logger

class RLTrainer:
    def __init__(self):
        self.state_size = len(settings.ML["features"])
        self.action_size = 3  # Buy, Sell, Hold
        self.gpu_available = len(tf.config.list_physical_devices('GPU')) > 0
        logger.info(f"GPU available: {self.gpu_available}")
        self.model = self.build_model()
        self.target_model = self.build_model()
        self.memory = deque(maxlen=2000)
        self.gamma = settings.RL["gamma"]
        self.epsilon = settings.RL["epsilon"]
        self.epsilon_min = 0.01
        self.epsilon_decay = settings.RL["epsilon_decay"]
        self.batch_size = settings.RL["batch_size"] * (4 if self.gpu_available else 1)  # Scale for GPU
        self.model_path = settings.RL["model_path"]

    def build_model(self):
        model = Sequential([
            Dense(128, input_dim=self.state_size, activation="relu"),
            Dense(64, activation="relu"),
            Dense(self.action_size, activation="linear")
        ])
        model.compile(loss="mse", optimizer=tf.keras.optimizers.Adam(learning_rate=settings.RL["learning_rate"]))
        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        state = np.array(state).reshape(1, -1)
        with tf.device('/GPU:0' if self.gpu_available else '/CPU:0'):
            act_values = self.model.predict(state, verbose=0)
        return np.argmax(act_values[0])

    def replay(self):
        if len(self.memory) < self.batch_size:
            return
        minibatch = random.sample(self.memory, self.batch_size)
        states = np.array([t[0] for t in minibatch])
        next_states = np.array([t[3] for t in minibatch])
        with tf.device('/GPU:0' if self.gpu_available else '/CPU:0'):
            targets = self.model.predict(states, verbose=0)
            next_qs = self.target_model.predict(next_states, verbose=0)
        for i, (state, action, reward, next_state, done) in enumerate(minibatch):
            target = reward
            if not done:
                target = reward + self.gamma * np.amax(next_qs[i])
            targets[i][action] = target
        with tf.device('/GPU:0' if self.gpu_available else '/CPU:0'):
            self.model.fit(states, targets, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    async def train(self, data):
        try:
            df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df = self.calculate_indicators(df)
            df = df.dropna()
            state = df[settings.ML["features"]].values
            for episode in range(settings.RL["episodes"]):
                for t in range(len(state) - 1):
                    current_state = state[t]
                    action = self.act(current_state)
                    next_state = state[t + 1]
                    reward = self.calculate_reward(df.iloc[t], action)
                    done = t == len(state) - 2
                    self.remember(current_state, action, reward, next_state, done)
                    self.replay()
                if episode % 10 == 0:
                    self.target_model.set_weights(self.model.get_weights())
                    logger.info(f"RL episode {episode} completed")
            self.model.save(self.model_path)
            logger.info(f"RL model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"RL training failed: {e}")
            raise

    def calculate_indicators(self, df):
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df["rsi_14"] = 100 - (100 / (1 + rs))
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["std_20"] = df["close"].rolling(window=20).std()
        df["bollinger_upper"] = df["sma_20"] + 2 * df["std_20"]
        df["bollinger_lower"] = df["sma_20"] - 2 * df["std_20"]
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["sentiment_score"] = 0.0
        df["whale_ratio"] = 0.0
        return df

    def calculate_reward(self, row, action):
        price_change = row["close"] - row["open"]
        fee = settings.TRADING["fees"]["taker"]
        if action == 0:  # Buy
            return price_change / row["open"] - fee
        elif action == 1:  # Sell
            return -price_change / row["open"] - fee
        return 0  # Hold

    def predict(self, data):
        try:
            df = pd.DataFrame([data], columns=["timestamp", "open", "high", "low", "close", "volume"])
            df = self.calculate_indicators(df)
            state = df[settings.ML["features"]].values[0]
            return self.act(state) / 2
        except Exception as e:
            logger.error(f"RL prediction failed: {e}")
            return 0.5

rl_trainer = RLTrainer()
