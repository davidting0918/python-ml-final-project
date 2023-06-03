import os
from flask_restful import Resource
from Base.ResponseCode import ResponseCode
from Module.Wordcloud import getWordCloud
from Module.ML_Sentimental.ml_model import train_model


class SentimentalAnalysisController(Resource):
    def __init__(self):
        pass

    def get(self):
        '''
        Get newest sentimental data
        '''
        twitter_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Module/ML_Sentimental/Crawler/twitter_data_new.csv')
        cvi_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Module/ML_Sentimental/CVIFolder/cvi_data.csv')
        model, sentiment_score = train_model(twitter_path, cvi_path)
        code = getWordCloud()

        response = {
            'sentiment_score': sentiment_score.to_json(),
            'word_cloud': code
        }
        return response
