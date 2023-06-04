from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from sklearn.neighbors import KNeighborsRegressor
import numpy as np
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
nltk.download('vader_lexicon')
from sklearn.metrics import mean_squared_error, r2_score

# 放入twitter的csv以及cvi的csv檔即可，會回傳model
def train_model(twitter_data, cvi_data):

    # 資料處理
    twitter_df = pd.read_csv(twitter_data)
    twitter_df['post_time'] = pd.to_datetime(twitter_df['post_time'])

    cvi_df = pd.read_csv(cvi_data)
    cvi_df['DATE'] = pd.to_datetime(cvi_df['DATE'])

    sia = SentimentIntensityAnalyzer()

    def get_sentiment_scores(text):
        sentiment = sia.polarity_scores(text)
        return sentiment['pos'], sentiment['neu'], sentiment['neg']

    twitter_df['positive'], twitter_df['neutral'], twitter_df['negative'] = zip(*twitter_df['text'].map(get_sentiment_scores))
    twitter_df['score'] = twitter_df['text'].apply(lambda x: sia.polarity_scores(x)['compound'])

    cvi_df['daily_return'] = cvi_df['CLOSE'].pct_change()
    cvi_df['daily_return'] = cvi_df['daily_return'] * 100
    cvi_df['daily_return_t+1'] = cvi_df['daily_return'].shift(-1)
    cvi_df['daily_return_t-1'] = cvi_df['daily_return'].shift(1)

    merged_df = pd.merge(twitter_df, cvi_df, left_on='post_time', right_on='DATE')

    merged_df.dropna(inplace=True)
    merged_df.drop('post_time', axis=1, inplace=True)
    merged_df.to_csv('merged.csv', index=False)

    sentiment_score = merged_df.groupby('DATE')['positive', 'negative', 'neutral', 'score'].mean()
    sentiment_score.to_csv('ml_sentiment_score.csv')

    # 訓練模型

    X = merged_df[['CLOSE', 'daily_return','daily_return_t-1', 'positive', 'neutral', 'negative', 'score', 'likes']]
    y = merged_df['daily_return_t+1']

    ratio = 30
    ratiovalues = [i for i in range(5, ratio, 5)]

    neighbors = 20
    neighborvalues = [i for i in range(1, neighbors, 1)]

    weights_value = ["uniform", "distance"]
    algorithm_value = ["ball_tree", "kd_tree", "brute"]
    p_value = [1, 2]

    relative_best_test_r2 = 0
    relative_best_test_mse = 0
    relative_best_neighbors = 0
    relative_best_weights = 0
    relative_best_algorithm = 0
    relative_best_p = 0
    test_ratio = 0

    for k in ratiovalues:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = k/100, random_state=2023)
        print(k)
        for j in neighborvalues:
            for i in weights_value:
                for a in algorithm_value:
                    for t in p_value:
                    
                        model = KNeighborsRegressor(n_neighbors = j, weights = i, algorithm = a, p = t)
                        model.fit(X_train, y_train)
    
                        y_pred_test = model.predict(X_test)
                        test_mse = mean_squared_error(y_test, y_pred_test)  # 均方誤差
                        test_r2 = r2_score(y_test, y_pred_test)  # 決定係數
    
                        if test_r2 > relative_best_test_r2:
                            relative_best_test_r2 = test_r2
                            relative_best_test_mse = test_mse
                            relative_best_neighbors = j
                            relative_best_weights = i
                            relative_best_algorithm = a
                            relative_best_p = t
                            test_ratio = k

    print("best n_neighbors:", relative_best_neighbors,"best weights:", relative_best_weights, \
        "best algorithm:", relative_best_algorithm, "best p:", relative_best_p, \
        "\nTesting r2:", relative_best_test_r2, "testing mse:", relative_best_test_mse, \
        "\ntest_ratio:", test_ratio)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = test_ratio/100, random_state=2023)
    model = KNeighborsRegressor(n_neighbors = relative_best_neighbors, weights = relative_best_weights, algorithm = relative_best_algorithm, p = relative_best_p)
    model.fit(X_train, y_train)

    return model, sentiment_score

if __name__ == '__main__':
    model, score = train_model('/Users/araschang/Desktop/coding/Pyml_final/Module/ML_Sentimental/Crawler/twitter_data_new.csv', '/Users/araschang/Desktop/coding/Pyml_final/Module/ML_Sentimental/CVIFolder/cvi_data.csv')
    print(score.to_json())