"""
ai-model/spending_predictor.py — ML pipeline for spending prediction + anomaly detection
Run: python spending_predictor.py --train --data path/to/transactions.csv
"""
import argparse, pickle, warnings
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
MODEL_DIR = Path("./models")
MODEL_DIR.mkdir(exist_ok=True)

FEATURE_COLS = ["expense_lag1","expense_lag2","expense_lag3","rolling3_mean","rolling3_std",
                "tx_count","avg_tx","max_tx","unique_cats","month_sin","month_cos"]

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"]  = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.month
    df["year"]  = df["date"].dt.year
    monthly = (df[df["type"]=="expense"]
        .groupby(["user_id","year","month"])
        .agg(total_expense=("amount","sum"),tx_count=("amount","count"),
             avg_tx=("amount","mean"),max_tx=("amount","max"),unique_cats=("category","nunique"))
        .reset_index().sort_values(["user_id","year","month"]))
    for lag in [1,2,3]:
        monthly[f"expense_lag{lag}"] = monthly.groupby("user_id")["total_expense"].shift(lag)
    monthly["rolling3_mean"] = monthly.groupby("user_id")["total_expense"].transform(lambda x: x.shift(1).rolling(3).mean())
    monthly["rolling3_std"]  = monthly.groupby("user_id")["total_expense"].transform(lambda x: x.shift(1).rolling(3).std())
    monthly["month_sin"] = np.sin(2*np.pi*monthly["month"]/12)
    monthly["month_cos"] = np.cos(2*np.pi*monthly["month"]/12)
    return monthly.dropna()

def train_prediction_model(df: pd.DataFrame):
    features = build_features(df)
    X, y = features[FEATURE_COLS], features["total_expense"]
    tscv = TimeSeriesSplit(n_splits=5)
    pipe = Pipeline([("scaler",StandardScaler()),("model",Ridge(alpha=1.0))])
    maes = []
    for tr,val in tscv.split(X):
        pipe.fit(X.iloc[tr],y.iloc[tr])
        maes.append(mean_absolute_error(y.iloc[val], pipe.predict(X.iloc[val])))
    pipe.fit(X, y)
    pickle.dump(pipe, open(MODEL_DIR/"spending_model.pkl","wb"))
    print(f"Prediction model saved | MAE={round(float(np.mean(maes)),2)}")

def train_anomaly_model(df: pd.DataFrame):
    expenses = df[df["type"]=="expense"].copy()
    cat_stats = expenses.groupby("category")["amount"].agg(["mean","std"]).reset_index()
    expenses  = expenses.merge(cat_stats, on="category")
    expenses["z_score"] = (expenses["amount"]-expenses["mean"])/expenses["std"].clip(lower=1)
    iso = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
    iso.fit(expenses[["amount","z_score"]].fillna(0))
    pickle.dump(iso, open(MODEL_DIR/"anomaly_model.pkl","wb"))
    print("Anomaly model saved")

def predict_next_month(user_transactions: List[Dict]) -> Dict:
    mp = MODEL_DIR/"spending_model.pkl"
    if not mp.exists(): return {"error":"Model not trained","predicted_total":0}
    pipe = pickle.load(open(mp,"rb"))
    df   = pd.DataFrame(user_transactions); df["user_id"] = "inf"
    feats = build_features(df)
    if feats.empty: return {"error":"Insufficient data","predicted_total":0}
    pred = float(pipe.predict(feats.tail(1)[FEATURE_COLS])[0])
    cat_totals = df[df["type"]=="expense"].groupby("category")["amount"].sum()
    total = cat_totals.sum()
    breakdown = [{"category":c,"predicted":round(pred*(a/total),2)} for c,a in cat_totals.sort_values(ascending=False).head(6).items()] if total else []
    return {"predicted_total":round(max(0,pred),2),"confidence":"high","breakdown":breakdown}

def detect_anomalies(user_transactions: List[Dict]) -> List[Dict]:
    mp = MODEL_DIR/"anomaly_model.pkl"
    if not mp.exists(): return []
    iso = pickle.load(open(mp,"rb"))
    df  = pd.DataFrame(user_transactions)
    exp = df[df["type"]=="expense"].copy()
    if exp.empty: return []
    cs  = exp.groupby("category")["amount"].agg(["mean","std"]).reset_index()
    exp = exp.merge(cs,on="category"); exp["z_score"]=(exp["amount"]-exp["mean"])/exp["std"].clip(lower=1)
    X   = exp[["amount","z_score"]].fillna(0)
    preds = iso.predict(X); scores = iso.score_samples(X)
    out = []
    for i,(p,s) in enumerate(zip(preds,scores)):
        if p==-1:
            r=exp.iloc[i]
            out.append({"id":r.get("id"),"amount":float(r["amount"]),"category":r["category"],"date":str(r.get("date","")),"anomaly_score":round(float(s),4)})
    return sorted(out,key=lambda x:x["anomaly_score"])[:10]

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--train",action="store_true"); p.add_argument("--data",default="data/transactions.csv")
    args=p.parse_args()
    if args.train:
        df=pd.read_csv(args.data,parse_dates=["date"])
        train_prediction_model(df); train_anomaly_model(df)
