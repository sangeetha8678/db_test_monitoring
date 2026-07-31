"""
Sliding Window Sequence Builder for Deep Learning Models (LSTM / GRU).
Builds time-series sequences of length N for lookback autoencoders and forecasting.
"""

def create_sliding_window_sequences(data, lookback=10):
    """
    Creates (X, y) sliding window sequences:
    X: [batch_size, lookback, features]
    y: [batch_size, features]
    """
    if not data or len(data) <= lookback:
        return [], []
    
    X, y = [], []
    for i in range(len(data) - lookback):
        X.append(data[i:i + lookback])
        y.append(data[i + lookback])
    return X, y
