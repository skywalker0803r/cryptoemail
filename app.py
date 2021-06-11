
import time
import pandas as pd
import numpy as np
import finlab_crypto
from finlab_crypto import Strategy
from finlab_crypto.overfitting import CSCV
import matplotlib.pyplot as plt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def send_message(title,text,email='skywalker0803r@gmail.com',password="yyzphzumdpnykjun"):
  content = MIMEMultipart()
  content["subject"] = title
  content["from"] = email
  content["to"] = email
  content.attach(MIMEText(text))
  with smtplib.SMTP(host="smtp.gmail.com", port="587") as smtp:
    smtp.ehlo()
    smtp.starttls()
    smtp.login(email,password)
    smtp.send_message(content)

# 回測優化
def Optimization(pair,freq):
  ohlcv = finlab_crypto.crawler.get_all_binance(pair,freq)
  @Strategy(sma1=20, sma2=60)
  def sma_strategy(ohlcv):
    close = ohlcv.close
    sma1 = close.rolling(sma_strategy.sma1).mean()
    sma2 = close.rolling(sma_strategy.sma2).mean()
    entries = (sma1 > sma2) & (sma1.shift() < sma2.shift())
    exits = (sma1 < sma2) & (sma1.shift() > sma2.shift())
    figures = {'overlaps': {'sma1': sma1,'sma1': sma2}}
    return entries, exits, figures
  variables = {
      'sma1': np.arange(10, 100, 5), 
      'sma2': np.arange(10, 100, 5),
      }
  portfolio = sma_strategy.backtest(ohlcv, variables=variables, freq=freq ,plot=False)
  cscv = CSCV(n_bins=10, objective=lambda r: r.mean())
  cscv.add_daily_returns(portfolio.daily_returns())
  cscv_result = cscv.estimate_overfitting(plot=False)
  pbo_test = str(cscv_result['pbo_test']*100)[:4]
  temp = portfolio.total_profit()[portfolio.total_profit()==portfolio.total_profit().max()].to_frame().reset_index()
  n1 = temp['sma1'].values[0]
  n2 = temp['sma2'].values[0]
  return n1,n2,pair,ohlcv,pbo_test

# 取得訊號
def GetSignal(n1,n2,pair,ohlcv):
  table = pd.DataFrame()
  table['close'] = ohlcv.close
  table['n1'] = ohlcv.close.rolling(n1).mean()
  table['n2'] = ohlcv.close.rolling(n2).mean()
  table['buy'] = ((table['n1'] > table['n2'])&(table['n1'].shift() < table['n2'].shift())).astype(int)
  table['sell'] = ((table['n1'] < table['n2'])&(table['n1'].shift() > table['n2'].shift())).astype(int)
  table = table.replace(0,np.nan)
  table = table.dropna(subset=['buy','sell'],how='all').tail(1)
  return table

def run():
    pair_list = ['BTCUSDT','ETHUSDT','LTCUSDT','BNBUSDT']
    freq = '4h'
    table_list = pd.DataFrame()
    for pair in pair_list:
        n1,n2,pair,ohlcv,pbo_test = Optimization(pair,freq)
        table = GetSignal(n1,n2,pair,ohlcv)
        table['pair'] = pair
        table_list = table_list.append(table)
    send_message(title='訊號通知',text = table_list.to_string())

# 主程序
if __name__ == "__main__":
    start = time.time() # 記錄當下時間當作起簡
    run() #先執行一次程式
    while True:
        if time.time() - start >= 3600*4: # 每隔四小時
            run() # 執行程式
            start = time.time() # 重新計時
    

    
