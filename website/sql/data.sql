PRAGMA foreign_keys = ON;

INSERT INTO users_current(username, ticker, shares, cost)
VALUES ('chinhau', 'AMC', 100, 12.08);

INSERT INTO users_current(username, ticker, shares, cost)
VALUES ('chinhau', 'MSFT', 50, 243.12);

INSERT INTO users_current(username, ticker, shares, cost)
VALUES ('chinhau', 'ORCL', 20, 76.23);

INSERT INTO users_current(username, ticker, shares, cost)
VALUES ('chinhau', 'PFE', 50, 35.96);

INSERT INTO users_current(username, ticker, shares, cost)
VALUES ('chinhau', 'UBER', 10, 40.12);

UPDATE users_finance SET cash = 6780 WHERE username = 'chinhau';

INSERT INTO users_feedback(username, title, comments)
VALUES ('nolan', 'I wish we could trade in real time.', 'Please make this happen!!')


