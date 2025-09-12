-- ユーザーテーブルの作成/更新
-- このSQLはシンプルな認証システム用のユーザーテーブルを作成します

-- ユーザーテーブルが存在しない場合は作成
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 既存のテーブルにis_adminカラムがない場合は追加
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'is_admin'
    ) THEN
        ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- 既存のテーブルに作成日時/更新日時カラムがない場合は追加
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'created_at'
    ) THEN
        ALTER TABLE users ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE users ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- 管理者ユーザーの追加（存在しない場合のみ）
-- ユーザー名: admin, パスワード: admin123
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM users WHERE username = 'admin'
    ) THEN
        INSERT INTO users (username, password, is_admin) 
        VALUES (
            'admin', 
            '$2b$12$HVdMUkYS7GKRaj5qV/sNcuA.QeZsUbL6LZUz3EtjlBrqDZ5NPJSom', -- admin123のハッシュ値
            TRUE
        );
    END IF;
END $$;
