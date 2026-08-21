"""Train an auditable baseline SDM with spatially separated train/test groups."""
from __future__ import annotations
import argparse
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score,roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from features import FEATURE_COLUMNS,TARGET_COLUMN

def main()->None:
    parser=argparse.ArgumentParser();parser.add_argument("csv",type=Path);parser.add_argument("--out",type=Path,default=Path("model.joblib"));parser.add_argument("--group-column",default="spatial_block");args=parser.parse_args()
    df=pd.read_csv(args.csv).dropna(subset=FEATURE_COLUMNS+[TARGET_COLUMN,args.group_column])
    train_idx,test_idx=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=42).split(df,groups=df[args.group_column]));train,test=df.iloc[train_idx],df.iloc[test_idx]
    model=HistGradientBoostingClassifier(max_iter=250,learning_rate=.06,max_leaf_nodes=24,l2_regularization=.5,random_state=42);model.fit(train[FEATURE_COLUMNS],train[TARGET_COLUMN]);p=model.predict_proba(test[FEATURE_COLUMNS])[:,1]
    print({"rows":len(df),"train_rows":len(train),"test_rows":len(test),"roc_auc":round(roc_auc_score(test[TARGET_COLUMN],p),4),"average_precision":round(average_precision_score(test[TARGET_COLUMN],p),4)})
    joblib.dump({"model":model,"features":FEATURE_COLUMNS},args.out)

if __name__=="__main__":main()
