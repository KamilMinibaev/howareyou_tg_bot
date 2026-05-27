-- init 
-- depends:

-- создаю таблицу юзеров со статусами
create table if not exists users_statuses (
    user_id     BIGINT PRIMARY KEY,
    status      VARCHAR
);


-- создаю таблицу с вопросами и ответами
create table if not exists user_answers (
    user_id         BIGINT REFERENCES users_statuses(user_id) ON DELETE CASCADE,
    created_dt      timestamp,
    answer_value    FLOAT,

    PRIMARY KEY (user_id, created_dt)
);
