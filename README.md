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
    - Users Table
      - name, password (hashed with hashlib sha512), email, age, exp, created.   
    - Users_Finance Table
    - Users_Historical Table
    - Users_Current Table
    - Users_Feedback Table
    - Users_Watchlist Table
    - Historical_Data Table
    - Feedback_Upvotes Table  


