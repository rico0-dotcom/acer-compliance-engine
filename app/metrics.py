import pandas as pd

def classification_metrics(rows):
    df=pd.DataFrame(rows)
    if df.empty:
        return {}
    y=df["expected_status"]
    p=df["predicted_status"]
    tp=((y=="PASS")&(p=="PASS")).sum()
    tn=((y=="FAIL")&(p=="FAIL")).sum()
    fp=((y=="FAIL")&(p=="PASS")).sum()
    fn=((y=="PASS")&(p=="FAIL")).sum()
    precision=tp/(tp+fp) if tp+fp else 0.0
    recall=tp/(tp+fn) if tp+fn else 0.0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
    accuracy=(p==y).mean()
    return {
        "accuracy":float(accuracy),
        "precision_pass":float(precision),
        "recall_pass":float(recall),
        "f1_pass":float(f1),
        "false_positive":int(fp),
        "false_negative":int(fn),
        "n":int(len(df)),
        "tn":int(tn)
    }
