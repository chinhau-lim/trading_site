# Stock Simulator that Recommends Stocks For You!

### Introduction

New to investing? Fed up with manual stock screening process? 
Here's a stock simulator that recommend stocks for users on a daily basis implemented with server-side dynamic pages. 

### Demo 

[![Website_Demo](demo.png)](https://vimeo.com/572867091)

### Built With
  - Python, Flask, SQL
  - Javascript, HTML
  - Chart.js, Plotly
  - Yahoo Finance API

### Database Schema

  - 9 Tables:
    - Users Table, collect users signup information/user verification purpose.
      - Columns: Name, Password (hashed with hashlib sha512), Email, Age, Exp, Created.   
    - Users_Finance Table, record the most-up-to-date purchasing power of each user.
      - Columns: Username, Cash    
    - Users_Historical Table, record each historical purchase of every user.
      - Columns: ID, Username, Ticker, Return, Status(Win/Flat/Loss)
    - Users_Current Table, record stocks that every user is currently holding.
      - Columns: Username, Ticker, Shares, Cost   
    - Users_Watchlist Table, record stocks that are on every user's watchlist.
      - Columns: Username, Ticker 
    - Historical_Data Table, record historical data for company's that release earnings.
      - Columns: Dates, Tickers, Company Name, URLs, Prev_Max, Curr_Max, Price_Diff, Percentage_Diff, Status(Win/Flat/Loss)   
    - Users_Feedback Table
      - Columns: UFID, Username, Title, Comments, Created   
    - Feedback_Upvotes Table  
      - Columns: UFID, Username 


