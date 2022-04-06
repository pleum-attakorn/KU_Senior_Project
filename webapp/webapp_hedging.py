from cProfile import label
import pandas as pd
import pickle
import numpy as np
import math
import datetime
from datetime import datetime
from scipy.stats import norm
from arch import arch_model
import streamlit as st
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

st.write("""
# Dynamic Hedging Algorithm for Fixed Coupon Note
""")

st.sidebar.header('Select 2 stocks')

def stock_input():
    stock1 = st.sidebar.selectbox('Stock1', ('ADVANC', 'AOT', 'BBL', 'BEM', 'BGRIM', 'BH', 'BJC', 'BTS', 'CBG', 'CPALL', 'CPF', 'CPN', 'DELTA', 'DTAC', 'EA', 'EGCO', 
    'GLOBAL', 'GPSC', 'GULF', 'HMPRO', 'INTUCH', 'IRPC', 'IVL', 'KBANK', 'KCE', 'KTB', 'KTC', 'LH', 'MINT', 'PTT', 'PTTEP', 'PTTGC', 'RATCH', 'SAWAD', 'SCB', 
    'SCC', 'STA', 'TISCO', 'TOP', 'TRUE') )
    stock2 = st.sidebar.selectbox('Stock2', ('AOT', 'ADVANC', 'BBL', 'BEM', 'BGRIM', 'BH', 'BJC', 'BTS', 'CBG', 'CPALL', 'CPF', 'CPN', 'DELTA', 'DTAC', 'EA', 'EGCO', 
    'GLOBAL', 'GPSC', 'GULF', 'HMPRO', 'INTUCH', 'IRPC', 'IVL', 'KBANK', 'KCE', 'KTB', 'KTC', 'LH', 'MINT', 'PTT', 'PTTEP', 'PTTGC', 'RATCH', 'SAWAD', 'SCB', 
    'SCC', 'STA', 'TISCO', 'TOP', 'TRUE') )
    stocks = [stock1, stock2]
    return stocks

def save(data , fn):
    with open(fn, 'wb') as f:
        pickle.dump(data, f)
def load(fn): 
    with open(fn, 'rb') as f:
        data = pickle.load(f)
        f.close()
    return data

class EuropeanCall:

    def call_delta(
        self, asset_price, asset_volatility, strike_price,
        time_to_expiration, risk_free_rate
            ):
        b = math.exp(-risk_free_rate*time_to_expiration)
        x1 = math.log(asset_price/(b*strike_price)) + .5*(asset_volatility*asset_volatility)*time_to_expiration
        x1 = x1/(asset_volatility*(time_to_expiration**.5))
        z1 = norm.cdf(x1)
        return z1
    
    def call_price(
        self, asset_price, asset_volatility, strike_price,
        time_to_expiration, risk_free_rate
            ):
        b = math.exp(-risk_free_rate*time_to_expiration)
        x1 = math.log(asset_price/(b*strike_price)) + .5*(asset_volatility*asset_volatility)*time_to_expiration           
        x1 = x1/(asset_volatility*(time_to_expiration**.5))
        z1 = norm.cdf(x1)
        z1 = z1*asset_price
        x2 = math.log(asset_price/(b*strike_price)) - .5*(asset_volatility*asset_volatility)*time_to_expiration
        x2 = x2/(asset_volatility*(time_to_expiration**.5))
        z2 = norm.cdf(x2)
        z2 = b*strike_price*z2
        return z1 - z2

    def __init__(
        self, asset_price, asset_volatility, strike_price,
        time_to_expiration, risk_free_rate
            ):
        self.asset_price = asset_price
        self.asset_volatility = asset_volatility
        self.strike_price = strike_price
        self.time_to_expiration = time_to_expiration
        self.risk_free_rate = risk_free_rate
        self.price = self.call_price(asset_price, asset_volatility, strike_price, time_to_expiration, risk_free_rate)
        self.delta = self.call_delta(asset_price, asset_volatility, strike_price, time_to_expiration, risk_free_rate)   
        
class EuropeanPut:

    def put_delta(
        self, asset_price, asset_volatility, strike_price,
        time_to_expiration, risk_free_rate
            ):
        b = math.exp(-risk_free_rate*time_to_expiration)
        x1 = math.log(asset_price/(b*strike_price)) + .5*(asset_volatility*asset_volatility)*time_to_expiration
        x1 = x1/(asset_volatility*(time_to_expiration**.5))
        z1 = norm.cdf(x1)
        return z1 - 1
    
    def put_price(
        self, asset_price, asset_volatility, strike_price,
        time_to_expiration, risk_free_rate
            ):
        b = math.exp(-risk_free_rate*time_to_expiration)
        x1 = math.log((b*strike_price)/asset_price) + .5*(asset_volatility*asset_volatility)*time_to_expiration
        x1 = x1/(asset_volatility*(time_to_expiration**.5))
        z1 = norm.cdf(x1)
        z1 = b*strike_price*z1
        x2 = math.log((b*strike_price)/asset_price) - .5*(asset_volatility*asset_volatility)*time_to_expiration
        x2 = x2/(asset_volatility*(time_to_expiration**.5))
        z2 = norm.cdf(x2)
        z2 = asset_price*z2
        return z1 - z2
    
    def __init__(
        self, asset_price, asset_volatility, strike_price,
        time_to_expiration, risk_free_rate
            ):
        self.asset_price = asset_price
        self.asset_volatility = asset_volatility
        self.strike_price = strike_price
        self.time_to_expiration = time_to_expiration
        self.risk_free_rate = risk_free_rate
        self.price = self.put_price(asset_price, asset_volatility, strike_price, time_to_expiration, risk_free_rate)
        self.delta = self.put_delta(asset_price, asset_volatility, strike_price, time_to_expiration, risk_free_rate)

def hedge(today_hedge, last_hedge, order):
    global long_cumulative, short_cumulative, long_share_held, short_DeltaxShare
    autocall = 0
    previous_hedge = today_hedge
    
    if last_hedge == today_hedge: # กรณีที่หุ้นที่ hedge เมื่อวานกับวันนี้คือหุ้นตัวเดียวกัน
        long_share_held = round(dic[today_hedge]['volumn']*dic[today_hedge]['long delta'][order])
        long_share_held = (long_share_held // 100) * 100
        d_long_share_held = long_share_held-long_share_helds[order-1] # เช็คว่าปริมาณหุ้นที่ถือเพื่อทำการ hedge ของวันนี้ มากกว่าหรือน้อยกว่าปริมาณหุ้นที่ถือเมื่อวาน
        
        if d_long_share_held <= 0: # ถ้าผลต่างเป็นลบ แปลว่าเราจะขายหุ้นที่ถือออกไป
            if d_long_share_held <= -100: # เช็คว่าหุ้นที่จะขายออกไป มีปริมาณมากกว่า100หรือไม่
                cost = dic[today_hedge]['price'][order]*d_long_share_held
                long_cumulative = long_cumulative+cost # เงินที่ได้จากการขายหุ้นออกไป จะนำไปหักล้างกับค่า cumulative
            elif d_long_share_held > -100: # ถ้าปริมาณหุ้นไม่ถึง 100 จะไม่เกิดการขาย hedge delta จะเท่าเดิมไม่เปลี่ยนแปลง
                dic[today_hedge]['long delta'][order] = dic[today_hedge]['long delta'][order-1]
                
        elif d_long_share_held > 0: # ถ้าผลต่างเป็นบวก แปลว่าเราจะซื้อหุ้นมาถือเพิ่ม
            if d_long_share_held >= 100: # เช็คว่าหุ้นที่จะซื้อ มีปริมาณมากกว่า100หรือไม่
                cost = dic[today_hedge]['price'][order]*d_long_share_held
                long_cumulative = long_cumulative+cost # เงินที่ใช้ซื้อหุ้นมาถือเพิ่ม จะนำไปรวมกับ cumulative
            elif d_long_share_held < 100: # ถ้าปริมาณหุ้นไม่ถึง 100 จะไม่เกิดการซื้อhedge delta จะเท่าเดิมไม่เปลี่ยนแปลง
                dic[today_hedge]['long delta'][order] = dic[today_hedge]['long delta'][order-1]
        
        long_cumulative = long_cumulative+funding_interests[order-1] # ค่า funding interest ของรอบที่แล้ว จะนำมารวมกับcumulative
        long_share_held = round(dic[today_hedge]['volumn']*dic[today_hedge]['long delta'][order]) # จำนวนหุ้นที่จะlong เพื่อ hedge
        long_share_held = (long_share_held // 100) * 100
        long_share_helds.append(long_share_held)
        long_cumulatives.append(round(long_cumulative))
        funding_interest = round(long_share_held*dic[today_hedge]['price'][order]*0.12/365) # funding interest
        funding_interests.append(funding_interest)
        PandL = - long_cumulative + long_share_held * dic[today_hedge]['price'][order] + notional
#p&lในส่วนของlong คิดจาก -1xcumulativeที่สะสมมา + จำนวนหุ้นที่ถืออยู่xราคาของหุ้นในวันนั้น + notional

        short_DeltaxShare = round(dic[today_hedge]['volumn']*dic[today_hedge]['short delta'][order])
        short_DeltaxShare = (short_DeltaxShare // 100) * 100
        d_short_DeltaxShare = short_DeltaxShare-short_DeltaxShares[order-1] # เช็คว่าปริมาณหุ้นที่เราจะshortเพื่อ hedge ของวันนี้ มากกว่าหรือน้อยกว่าปริมาณหุ้นเมื่อวาน
        if d_short_DeltaxShare < 0: # ถ้าผลต่างเป็นลบ แปลว่าเราจะซื้อหุ้นมาคืนบางส่วน
            if d_short_DeltaxShare <= -100: # เช็คว่าหุ้นที่จะซื้อมาคืน มีปริมาณมากกว่า100หรือไม่
                cost = dic[today_hedge]['price'][order]*d_short_DeltaxShare
                short_cumulative = short_cumulative+cost # เงินที่ใช้ในการซื้อหุ้นคืน จะนำไปหักล้างกับค่า cumulative
            elif d_short_DeltaxShare > -100: # ถ้าปริมาณหุ้นไม่ถึง 100 จะไม่เกิดการซื้อหุ้นมาคืน hedge delta จะเท่าเดิมไม่เปลี่ยนแปลง
                dic[today_hedge]['short delta'][order] = dic[today_hedge]['short delta'][order-1]
        elif d_short_DeltaxShare > 0: # ถ้าผลต่างเป็นบวก แปลว่าเราจะshortหุ้นเพิ่ม
            if d_short_DeltaxShare > 100: # เช็คว่าหุ้นที่จะshort มีปริมาณมากกว่า100หรือไม่
                cost = dic[today_hedge]['price'][order]*d_short_DeltaxShare
                short_cumulative = short_cumulative+cost # เงินที่ได้จากการshortหุ้น จะนำไปรวมกับ cumulative
            elif d_short_DeltaxShare < 100: # ถ้าปริมาณหุ้นไม่ถึง 100 จะไม่เกิดการshort hedge delta จะเท่าเดิมไม่เปลี่ยนแปลง
                dic[today_hedge]['short delta'][order] = dic[today_hedge]['short delta'][order-1]
        
        short_DeltaxShare = round(dic[today_hedge]['volumn']*dic[today_hedge]['short delta'][order]) # จำนวนหุ้นที่จะshort เพื่อ hedge
        short_DeltaxShare = (short_DeltaxShare // 100) * 100
        short_DeltaxShares.append(short_DeltaxShare)
        short_cumulatives.append(round(short_cumulative))
        PandL = PandL + short_cumulative - short_DeltaxShare * dic[today_hedge]['price'][order]
#p&lในส่วนของshort คิดจาก cumulativeที่สะสมมา - จำนวนหุ้นที่ต้องซื้อมาคืนxราคาของหุ้นในวันนั้น

        if observ[order] == 1 and order != len(day2)-1: # กรณีที่เป็นวัน observation date
            count = 0
            for j in range(0, len(stock)):
                if dic[stock[j]]['price'][order] > dic[stock[j]]['autocall']:
                    count = count + 1
            if count == len(stock):
                autocall = 1
            if autocall == 1:
                PandL = -long_cumulative + long_share_held * dic[today_hedge]['price'][order] - notional
#p&lในส่วนของlong คิดจาก -1xcumulativeที่สะสมมา + จำนวนหุ้นที่ถืออยู่xราคาของหุ้นในวันนั้น - notional
                PandL = PandL + short_cumulative - short_DeltaxShare * dic[today_hedge]['price'][order]
#p&lในส่วนของshort คิดจาก cumulativeที่สะสมมา - จำนวนหุ้นที่ต้องซื้อมาคืนxราคาของหุ้นในวันนั้น
                PandL = PandL - r*notional #หักล้างค่าดอกเบี้ยที่ต้องจ่ายให้นักลงทุน
            elif autocall == 0:
                PandL = PandL - r*notional #หักล้างค่าดอกเบี้ยที่ต้องจ่ายให้นักลงทุน
        
        elif observ[order] == 1 and order == len(day2)-1: # กรณีที่เป็นวันครบกำหนด
            maxdiff = 0
            target_stock = ''
            for j in range(0, len(stock)):
                if dic[stock[j]]['price'][order] <= dic[stock[j]]['strike price']:
                    if dic[stock[j]]['strike price'] - dic[stock[j]]['price'][order] > maxdiff:
                        maxdiff = dic[stock[j]]['strike price'] - dic[stock[j]]['price'][order]
                        target_stock = stock[j]
            
            if maxdiff == 0:
                PandL = -long_cumulative + long_share_held * dic[today_hedge]['price'][order] - notional
#p&lในส่วนของlong คิดจาก -1xcumulativeที่สะสมมา + จำนวนหุ้นที่ถืออยู่xราคาของหุ้นในวันนั้น - notional
                PandL = PandL + short_cumulative - short_DeltaxShare * dic[today_hedge]['price'][order]
#p&lในส่วนของshort คิดจาก cumulativeที่สะสมมา - จำนวนหุ้นที่ต้องซื้อมาคืนxราคาของหุ้นในวันนั้น
                PandL = PandL - r*notional #หักล้างค่าดอกเบี้ยที่ต้องจ่ายให้นักลงทุน
            else:
                if today_hedge == target_stock:
                    PandL = -long_cumulative - (dic[target_stock]['volumn'] - long_share_held) * dic[target_stock]['price'][order] + notional
#p&lในส่วนของlong คิดจาก -1xcumulativeที่สะสมมา - จำนวนหุ้นต้องซื้อมาเพื่อให้หุ้นครบตามจำนวนที่จะมอบให้นักลงทุนxราคาของหุ้นในวันนั้น + notional
                    PandL = PandL + short_cumulative - short_DeltaxShare * dic[target_stock]['price'][order]
#p&lในส่วนของshort คิดจาก cumulativeที่สะสมมา - จำนวนหุ้นที่ต้องซื้อมาคืนxราคาของหุ้นในวันนั้น
                    PandL = PandL - r*notional #หักล้างค่าดอกเบี้ยที่ต้องจ่ายให้นักลงทุน
                
                elif today_hedge != target_stock:
                    PandL = -long_cumulative + long_share_held * dic[today_hedge]['price'][order] + notional
#p&lในส่วนของlong คิดจาก -1xcumulativeที่สะสมมา + จำนวนหุ้นที่ถืออยู่xราคาของหุ้นในวันนั้น + notional
                    PandL = PandL + short_cumulative - short_DeltaxShare * dic[today_hedge]['price'][order]
#p&lในส่วนของshort คิดจาก cumulativeที่สะสมมา - จำนวนหุ้นที่ต้องซื้อมาคืนxราคาของหุ้นในวันนั้น
                    PandL = PandL - r*notional #หักล้างค่าดอกเบี้ยที่ต้องจ่ายให้นักลงทุน
                    PandL = PandL - dic[target_stock]['volumn'] * dic[target_stock]['price'][order] #หักล้างเงินจำนวนเงินที่ใช้ซื้อหุ้น PTTEP มามอบให้นักลงทุน
        PandLs.append(round(PandL))
        
    elif last_hedge != today_hedge: # กรณีที่หุ้นที่จะ hedge คนละตัวกับหุ้นที่ hedge เมื่อวาน
        #จัดการหุ้นตัวที่เรา hedge ไว้ก่อนหน้านี้
        previous_PandL = - long_cumulative + long_share_held * dic[last_hedge]['price'][order] + notional
        previous_PandL = previous_PandL + short_cumulative - short_DeltaxShare * dic[last_hedge]['price'][order]
        
        long_share_held = round(dic[today_hedge]['volumn']*dic[today_hedge]['long delta'][order]) # จำนวนหุ้นที่จะlong เพื่อ hedge
        long_share_held = (long_share_held // 100) * 100
        long_cumulative = round(long_share_held*dic[today_hedge]['price'][order]) # เงินที่ต้องใช้ในการซื้อหุ้นมาถือเพื่อ hedge
        long_cumulative = long_cumulative+funding_interests[order-1] # ค่า funding interest ของรอบที่แล้ว จะนำมารวมกับcumulative
        long_share_helds.append(long_share_held)
        long_cumulatives.append(round(long_cumulative))
        funding_interest = round(long_share_held*dic[today_hedge]['price'][order]*0.12/365) # ค่า funding interest
        funding_interests.append(funding_interest)
        PandL = previous_PandL - long_cumulative + long_share_held * dic[today_hedge]['price'][order] + notional
#p&lในส่วนของlong คิดจาก -1xcumulativeที่สะสมมา + จำนวนหุ้นที่ถืออยู่xราคาของหุ้นในวันนั้น + notional

        short_DeltaxShare = round(dic[today_hedge]['volumn']*dic[today_hedge]['short delta'][order]) # จำนวนหุ้นที่จะshort เพื่อ hedge
        short_DeltaxShare = (short_DeltaxShare // 100) * 100
        short_cumulative = round(short_DeltaxShare*dic[today_hedge]['price'][order]) # เงินที่ได้จากการshortหุ้นเพื่อ hedge
        short_DeltaxShares.append(short_DeltaxShare)
        short_cumulatives.append(round(short_cumulative))
        PandL = PandL + short_cumulative - short_DeltaxShare * dic[today_hedge]['price'][order]
#p&lในส่วนของshort คิดจาก cumulativeที่สะสมมา - จำนวนหุ้นที่ต้องซื้อมาคืนxราคาของหุ้นในวันนั้น

        if observ[order] == 1 and order != len(day2)-1: # กรณีที่เป็นวัน observation date
            count = 0
            for j in range(0, len(stock)):
                if dic[stock[j]]['price'][order] > dic[stock[j]]['autocall']:
                    count = count + 1
            if count == len(stock):
                autocall = 1
            if autocall == 1:
                PandL = previous_PandL -long_cumulative + long_share_held * dic[today_hedge]['price'][order] - notional
#p&lในส่วนของlong คิดจาก -1xcumulativeที่สะสมมา + จำนวนหุ้นที่ถืออยู่xราคาของหุ้นในวันนั้น - notional
                PandL = PandL + short_cumulative - short_DeltaxShare * dic[today_hedge]['price'][order]
#p&lในส่วนของshort คิดจาก cumulativeที่สะสมมา - จำนวนหุ้นที่ต้องซื้อมาคืนxราคาของหุ้นในวันนั้น
                PandL = PandL - r*notional #หักล้างค่าดอกเบี้ยที่ต้องจ่ายให้นักลงทุน
            elif autocall == 0:
                PandL = PandL - r*notional #หักล้างค่าดอกเบี้ยที่ต้องจ่ายให้นักลงทุน
                
        elif observ[order] == 1 and order == len(day2)-1: # กรณีที่เป็นวันครบกำหนด
            maxdiff = 0
            target_stock = ''
            for j in range(0, len(stock)):
                if dic[stock[j]]['price'][order] <= dic[stock[j]]['strike price']:
                    if dic[stock[j]]['strike price'] - dic[stock[j]]['price'][order] > maxdiff:
                        maxdiff = dic[stock[j]]['strike price'] - dic[stock[j]]['price'][order]
                        target_stock = stock[j]
            
            if maxdiff == 0:
                PandL = previous_PandL - long_cumulative + long_share_held * dic[today_hedge]['price'][order] - notional
#p&lในส่วนของlong คิดจาก -1xcumulativeที่สะสมมา + จำนวนหุ้นที่ถืออยู่xราคาของหุ้นในวันนั้น - notional
                PandL = PandL + short_cumulative - short_DeltaxShare * dic[today_hedge]['price'][order]
#p&lในส่วนของshort คิดจาก cumulativeที่สะสมมา - จำนวนหุ้นที่ต้องซื้อมาคืนxราคาของหุ้นในวันนั้น
                PandL = PandL - r*notional #หักล้างค่าดอกเบี้ยที่ต้องจ่ายให้นักลงทุน
            else:
                if today_hedge == target_stock:
                    PandL = previous_PandL - long_cumulative - (dic[target_stock]['volumn'] - long_share_held) * dic[target_stock]['price'][order] + notional
#p&lในส่วนของlong คิดจาก -1xcumulativeที่สะสมมา - จำนวนหุ้นต้องซื้อมาเพื่อให้หุ้นครบตามจำนวนที่จะมอบให้นักลงทุนxราคาของหุ้นในวันนั้น + notional
                    PandL = PandL + short_cumulative - short_DeltaxShare * dic[target_stock]['price'][order]
#p&lในส่วนของshort คิดจาก cumulativeที่สะสมมา - จำนวนหุ้นที่ต้องซื้อมาคืนxราคาของหุ้นในวันนั้น
                    PandL = PandL - r*notional #หักล้างค่าดอกเบี้ยที่ต้องจ่ายให้นักลงทุน
                
                elif today_hedge != target_stock:
                    PandL = -long_cumulative + long_share_held * dic[today_hedge]['price'][order] + notional
#p&lในส่วนของlong คิดจาก -1xcumulativeที่สะสมมา + จำนวนหุ้นที่ถืออยู่xราคาของหุ้นในวันนั้น + notional
                    PandL = PandL + short_cumulative - short_DeltaxShare * dic[today_hedge]['price'][order]
#p&lในส่วนของshort คิดจาก cumulativeที่สะสมมา - จำนวนหุ้นที่ต้องซื้อมาคืนxราคาของหุ้นในวันนั้น
                    PandL = PandL - r*notional #หักล้างค่าดอกเบี้ยที่ต้องจ่ายให้นักลงทุน
                    PandL = PandL - dic[target_stock]['volumn'] * dic[target_stock]['price'][order] #หักล้างเงินจำนวนเงินที่ใช้ซื้อหุ้น PTTEP มามอบให้นักลงทุน
        PandLs.append(round(PandL))
        
    return autocall


stock = stock_input()
dic = {}
if st.button('Start hedging'):    
    st.write('stock1 = ', stock[0])
    st.write('stock2 = ', stock[1])
    for i in range(0, len(stock)):
        dic[stock[i]] = {}
    
    #historical volatility
    for i in range(0, len(stock)):
        direc = "../SET50 JAN_JULY/" + stock[i] + ".pkl"
        data = load(direc)
        histo_price = []
        past_day = []

        #ข้อมูลราคาหุ้นในเดือนแรกที่จะนำมาคิด historical volatility
        for j in data['TRADE'].keys():
            if j == '20190201':
                break
            histo_price.append(data['TRADE'][j]["Price"].iloc[-1])
            past_day.append(j)

        #แปลงข้อมูลวันที่จาก str เป็น datetime
        past_day2 = []
        for j in past_day:
            time = f'{j[0:4]}-{j[4:6]}-{j[6:]}'
            date_time_obj = datetime.strptime(time, '%Y-%m-%d')
            past_day2.append(date_time_obj)

        his_price = pd.DataFrame(
            {"historical price": histo_price,
            },
            index=past_day2)

        # คิด daily return ของ PTTEP
        his_price['Return'] = his_price['historical price'].pct_change()
        # คิด log return ของ PTTEP และปรับสเกลด้วยการคูณ 100
        his_price['Return'] = 100*np.log(1 + his_price['Return'])
        # แปลงข้อมูลจาก dataframe เป็น array
        data2 = his_price['Return'].to_numpy()
        data2 = data2[np.logical_not(np.isnan(data2))]  # ตัดข้อมูลที่เป็น nan ออก
        n_test = 1  # ข้อมูล historical volatility จะอยู่ในวันสุดท้าย
        train, test = data2[:-n_test], data2[-n_test:]
        model = arch_model(train, mean='Zero', vol='GARCH', p=1, q=1)
        model_fit = model.fit()
        predictions = model_fit.forecast(horizon=n_test)
        histo_vol = float("{:.2f}".format(float(
            (predictions.variance.values[-1, :])**0.5 * np.sqrt(252))))  # คิดค่า historical volatility
        dic[stock[i]]['historical volatility'] = histo_vol

    #ราคาหุ้นในช่วงสัญญา
    for i in range(0, len(stock)):
        price = []
        day = []
        check = 0

        direc = "../SET50 JAN_JULY/" + stock[i] + ".pkl"
        data = load(direc)

        for j in data['TRADE'].keys():
            if j == '20190201':
                check = 1
            if check != 1:
                continue
            price.append(data['TRADE'][j]["Price"].iloc[-1])
            day.append(j)

        dic[stock[i]]['price'] = price

    observ = []
    #วันที่เป็น observation date และวันครบกำหนด
    for j in range(0, len(day)):
        if j == 0 or j == len(day)-1:
            observ.append(1)

        elif j != len(day)-1 and day[j][4:6] != day[j+1][4:6]:
            observ.append(1)
        else:
            observ.append(0)
    
    #volatility แต่ละวันในช่วงสัญญา
    for i in range(0, len(stock)):
        vol = []
        price = dic[stock[i]]['price']

        direc = "../SET50 JAN_JULY/" + stock[i] + ".pkl"
        data = load(direc)
        histo_price = []

        for j in data['TRADE'].keys():
            if j == '20190201':
                break
            histo_price.append(data['TRADE'][j]["Price"].iloc[-1])

        for j in range(0, len(price)):
            histo_price.append(price[j])
            his_price = pd.DataFrame(
                {"historical price": histo_price,
                },
            )
            # คิด daily return ของ PTTEP
            his_price['Return'] = his_price['historical price'].pct_change()
            # คิด log return ของ PTTEP และปรับสเกลด้วยการคูณ 100
            his_price['Return'] = 100*np.log(1 + his_price['Return'])
            # แปลงข้อมูลจาก dataframe เป็น array
            data2 = his_price['Return'].to_numpy()
            # ตัดข้อมูลที่เป็น nan ออก
            data2 = data2[np.logical_not(np.isnan(data2))]
            n_test = 1  # ข้อมูล historical volatility จะอยู่ในวันสุดท้าย
            train, test = data2[:-n_test], data2[-n_test:]
            model = arch_model(train, mean='Zero', vol='GARCH', p=1, q=1)
            model_fit = model.fit()
            predictions = model_fit.forecast(horizon=n_test)
            histo_vol = float("{:.2f}".format(float(
                (predictions.variance.values[-1, :])**0.5 * np.sqrt(252))))  # คิดค่า historical volatility
            vol.append(histo_vol)  # คิดค่า historical volatility

        dic[stock[i]]['volatility'] = vol

    #แปลงข้อมูลวันที่จาก str เป็น datetime
    day2 = []
    for i in day:
        time = f'{i[0:4]}-{i[4:6]}-{i[6:]}'
        date_time_obj = datetime.strptime(time, '%Y-%m-%d')
        day2.append(date_time_obj)

    start_date = day2[0]  # วันที่ริ่มสัญญา
    ex = day2[len(day2)-1]  # วันครบกำหนด
    total = ex-start_date  # จำนวนวันทั้งหมด ตั้งแต่วันแรกถึงวันครบกำหนด
    notional = 10000000
    r = 0.12/12
    # คิดเวลาที่เหลืออยู่จนถึงวันครบกำหนดของแต่ละวันในช่วงสัญญา
    time = []
    for i in range(0, len(day2)):
        date = day2[i]
        t = ex-date
        if t.days == 0:
            time.append(1)
            continue
        time.append(t.days)
    
    for i in range(0, len(stock)):
        start_price = dic[stock[i]]['price'][0]
        dic[stock[i]]['autocall'] = 0.90 * start_price  # autocall
        dic[stock[i]]['strike price'] = 0.85 * start_price  # strike price

        long_deltas = []
        short_deltas = []

        for j in range(0, len(day2)):
            call = EuropeanCall(dic[stock[i]]['price'][j], dic[stock[i]]['volatility']
                                [j]*1.05/100, dic[stock[i]]['strike price'], time[j]/365, 0.12)
            put = EuropeanPut(dic[stock[i]]['price'][j], dic[stock[i]]['volatility']
                            [j]*1.2/100, dic[stock[i]]['strike price'], time[j]/365, 0.12)
            long_deltas.append(call.delta)
            short_deltas.append(-1*put.delta)

        dic[stock[i]]['long delta'] = long_deltas
        dic[stock[i]]['short delta'] = short_deltas
        # จำนวนหุ้นที่จะมอบให้นักลงทุน ถ้าราคาหุ้นในวันครบกำหนดน้อยกว่า strike price
        volumn = math.floor(notional/dic[stock[i]]['strike price'])
        dic[stock[i]]['volumn'] = (volumn//100)*100

    firststock = ''
    maxhisto = 0
    for i in range(0, len(stock)):
        if dic[stock[i]]['historical volatility'] > maxhisto:
            maxhisto = dic[stock[i]]['historical volatility']
            firststock = stock[i]

    long_share_held = round(dic[firststock]['volumn'] * dic[firststock]['long delta'][0]) # จำนวนหุ้นที่จะlong เพื่อ hedge ในวันแรก
    long_share_held = (long_share_held // 100) * 100 # เงินที่ต้องใช้ในการซื้อหุ้นมาถือเพื่อ hedge ในวันแรก
    long_cumulative = round(long_share_held*dic[firststock]['price'][0])    
    funding_interest = round(long_cumulative*0.12/365) # funding interest จากการซื้อหุ้นของวันแรก    
    short_DeltaxShare = round(dic[firststock]['volumn']*dic[firststock]['short delta'][0]) # จำนวนหุ้นที่จะshort เพื่อ hedge ในวันแรก
    short_DeltaxShare = (short_DeltaxShare // 100) * 100    
    short_cumulative = round(short_DeltaxShare*dic[firststock]['price'][0]) # เงินที่ได้จากการshortหุ้นเพื่อ hedge ในวันแรก
    long_share_helds = []
    funding_interests = []
    long_cumulatives = []
    ticker = []
    price = []
    long_delta = []
    short_delta = []
    short_DeltaxShares = []
    short_cumulatives = []
    PandLs = []
    long_share_helds.append(long_share_held)
    funding_interests.append(funding_interest)
    long_cumulatives.append(long_cumulative)
    ticker.append(firststock)
    price.append(dic[firststock]['price'][0])
    long_delta.append(dic[firststock]['long delta'][0])
    short_delta.append(dic[firststock]['short delta'][0])
    short_DeltaxShares.append(short_DeltaxShare)
    short_cumulatives.append(short_cumulative)
    PandLs.append(round(notional))  # profit and loss ของวันแรก เท่ากับ notional

    previous_hedge = firststock
    for i in range(1, len(day2)):
        target = ''
        maxvol = 0
        for j in range(0, len(stock)):
            if dic[stock[j]]['volatility'][i] > maxvol:
                maxvol = dic[stock[j]]['volatility'][i]
                target = stock[j]
        ticker.append(target)  # ชื่อหุ้น
        price.append(dic[target]['price'][i])  # ราคาหุ้นวันนี้
        long_delta.append(dic[target]['long delta'][i])  # long delta
        short_delta.append(dic[target]['short delta'][i])  # short delta
        autocall_check = hedge(target, previous_hedge, i)
        if autocall_check == 1:  # กรณีที่เป็น autocall
            #print('Auto Call in date :', day2[i])
            st.write('Auto Call in date : ', day2[i])
            break
    
    df = pd.DataFrame(
        {"stock": ticker,
         "asset price": price,
         "long delta": long_delta,
         "long share held": long_share_helds,
         "long cumulative": long_cumulatives,
         "short delta": short_delta,
         "short DeltaxShare": short_DeltaxShares,
         "short cumulative": short_cumulatives,
         "profit and loss": PandLs,
         },
        index=day2[:len(PandLs)])
    
    st.subheader('Hedging Detail')
    st.write(df)
    for i in range(0, len(stock)):
        st.subheader(stock[i], 'Price')
        fig = plt.subplots(figsize=(12, 8))
        plt.plot(day2[:len(PandLs)] , dic[stock[i]]['price'][:len(PandLs)])
        plt.axhline(y=dic[stock[i]]['autocall'], linestyle='-', label='autocall', color='red')
        plt.axhline(y=dic[stock[i]]['strike price'], linestyle='-', label='strike price', color='yellow')
        for j in range(1, len(PandLs)):
            if observ[j] == 1 or j == len(day2)-1:
                plt.axvline(x=day2[j], linestyle='-', color='green')
        plt.title(stock[i])
        plt.xlabel("date")
        plt.ylabel("price")
        plt.legend()
        plt.savefig('x',dpi=400)
        st.image('x.png')
        os.remove('x.png')

    st.subheader('Stocks Volatility')
    fig = plt.subplots(figsize=(12, 8))
    for i in range(0, len(stock)):
        plt.plot(day2[:len(PandLs)] , dic[stock[i]]['volatility'][:len(PandLs)], label=stock[i])
    plt.title('Volatility')
    plt.xlabel("date")
    plt.ylabel("volatility")
    plt.legend()
    plt.savefig('x',dpi=400)
    st.image('x.png')
    os.remove('x.png')

    st.subheader('Profit and Loss')
    st.write('profit and loss = ', PandLs[len(PandLs)-1])
