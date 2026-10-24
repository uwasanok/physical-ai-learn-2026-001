"""Small supervised language classifier. No API keys, LLM, or GPU required."""
import json
from pathlib import Path
import joblib
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
TRAIN = {
    'inspection': ['点検地点へ行って', '点検をお願いします', '点検エリアまで移動', '点検場所に向かって', '点検ポイントへ進んで', '点検のところに行く', '点検場所へ移動して', '点検しに行ってください', '点検エリアへ向かう', '点検地点を目指して'],
    'supply': ['備品地点へ行って', '備品を取りに行って', '備品エリアまで移動', '備品場所に向かって', '備品ポイントへ進んで', '備品のところに行く', '備品場所へ移動して', '備品の場所に行ってください', '備品エリアへ向かう', '備品地点を目指して'],
    'home': ['ホームへ戻って', 'ホームに帰って', 'ホームまで移動', 'ホームに向かって', '出発地点に戻って', '出発場所に帰る', '出発地点へ移動して', '出発した場所に戻ってください', 'ホームを目指して', '出発地点まで帰って'],
    'stop': ['停止して', '止まって', '今すぐ止めて', 'ストップ', 'その場で停止', '動かないで', '走行を停止して', '移動を止めてください', '緊急停止', 'その場で止まってください'],
}
# Authored holdout sentences: never passed to fit(). Limited vocabulary, not a general benchmark.
TEST = [('点検エリアへ移動してください','inspection'), ('点検地点で待って','inspection'),
        ('備品の場所まで進んでください','supply'), ('備品エリアに行きたい','supply'),
        ('ホームに戻ってください','home'), ('出発地点に帰りたい','home'),
        ('いったん停止してください','stop'), ('ここで止まって','stop')]

def predict(model, text):
    probabilities = model.predict_proba([text])[0]
    index = int(np.argmax(probabilities))
    confidence = float(probabilities[index])
    # A conservative abstention policy; not a guarantee against all out-of-domain phrases.
    label = str(model.classes_[index]) if confidence >= 0.60 else 'unknown'
    return label, confidence

def train():
    model = make_pipeline(TfidfVectorizer(analyzer='char', ngram_range=(1,3)),
                          LogisticRegression(C=15, max_iter=1000, random_state=42))
    texts, labels = zip(*[(text,label) for label,items in TRAIN.items() for text in items])
    model.fit(texts, labels)
    out=ROOT/'output'; out.mkdir(exist_ok=True)
    joblib.dump(model, out/'intent_model.joblib')
    rows=[{'text':t,'expected':e,'predicted':predict(model,t)[0],'confidence':predict(model,t)[1]} for t,e in TEST]
    unknown=[{'text':t,'predicted':predict(model,t)[0],'confidence':predict(model,t)[1]} for t in ['こんにちは','明日の天気は','ダンスを踊って']]
    metrics={'training_examples':len(texts),'test_examples':len(rows),'correct':sum(r['expected']==r['predicted'] for r in rows),'test':rows,'out_of_domain':unknown,'threshold':0.60,'seed':42,'limitation':'Small authored holdout, vocabulary close to training. Not general Japanese understanding.'}
    (out/'intent_evaluation.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(metrics,ensure_ascii=False,indent=2))
    return model

if __name__ == '__main__': train()
