from flask_restful import Api
from flask import Flask
from Routes.DataScienceController import SentimentalAnalysisController

app = Flask(__name__)
api = Api(app)

api.add_resource(
    SentimentalAnalysisController,
    '/sentiment',
)
