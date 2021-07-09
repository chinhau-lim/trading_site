-- This code is developed by Chin Hau Lim.

CREATE TABLE users(
	name VARCHAR(20) NOT NULL,
	password VARCHAR(256) NOT NULL,
	email VARCHAR(50) NOT NULL,
	age INTEGER NOT NULL,
	exp INTEGER NOT NULL, 
	created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY(name)
);


CREATE TABLE stocks(
	dates TEXT NOT NULL,
	tickers VARCHAR(10) NOT NULL, 
	company_name VARCHAR(200) NOT NULL,
	urls VARCHAR(65535) NOT NULL,
	eps_estimate DECIMAL(10,2),
	reported_eps DECIMAL(10,2),
	surprise DECIMAL(10, 2),
	prev_max DECIMAL(10, 2), 
	curr_max DECIMAL(10, 2),
	price_diff DECIMAL(10, 2),
	percentage_diff DECIMAL(10, 2),
	status INTEGER NOT NULL CHECK (status IN (0, 1, 2)),
	PRIMARY KEY(dates, tickers)
);

CREATE TABLE users_watchlist(
	username VARCHAR(20) NOT NULL,
	ticker VARCHAR(10) NOT NULL, 
	PRIMARY KEY(username, ticker),
	FOREIGN KEY (username) REFERENCES users(name)
);

CREATE TABLE users_current(
	username VARCHAR(20) NOT NULL,
	ticker VARCHAR(20) NOT NULL, 
	shares INTEGER NOT NULL,
	cost DECIMAL(15, 2) NOT NULL,
	PRIMARY KEY(username, ticker),
	FOREIGN KEY (username) REFERENCES users(name)
);

CREATE TABLE users_historical(
	uhid INTEGER AUTO_INCREMENT,
	username VARCHAR(20) NOT NULL,
	ticker VARCHAR(20) NOT NULL,
	return DECIMAL(15, 2) NOT NULL, 
	status INTEGER NOT NULL CHECK (status IN (0, 1, 2)),
	PRIMARY KEY(uhid),
	FOREIGN KEY (username) REFERENCES users(name)
);

CREATE TABLE users_finance(
	username VARCHAR(20) NOT NULL,
	cash DECIMAL(15, 2) NOT NULL, 
	PRIMARY KEY(username),
	FOREIGN KEY (username) REFERENCES users(name)
);

CREATE TABLE users_feedback(
	ufid INTEGER PRIMARY KEY AUTOINCREMENT,
	username VARCHAR(20) NOT NULL,
	title VARCHAR(400) NOT NULL, 
	comments TEXT NOT NULL, 
	created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (username) REFERENCES users(name)
);

CREATE TABLE feedback_upvotes(
	ufid INT NOT NULL,
	username VARCHAR(20) NOT NULL,
	PRIMARY KEY(ufid, username),
	FOREIGN KEY (ufid) REFERENCES users_feedback(ufid),
	FOREIGN KEY (username) REFERENCES users(name)
);
