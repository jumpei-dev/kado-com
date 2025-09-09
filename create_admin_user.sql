-- 管理者ユーザー作成スクリプト
-- 管理者権限を持つユーザーを作成

-- パスワードのハッシュ: "admin123" のハッシュ値
-- bcryptによるハッシュ化（実際のアプリケーションで使用されているアルゴリズムと合わせています）
DO $$
DECLARE
  admin_exists INTEGER;
BEGIN
  -- 既存の管理者ユーザーをチェック
  SELECT COUNT(*) INTO admin_exists FROM users WHERE name = 'admin';
  
  -- 管理者ユーザーが存在しない場合は作成
  IF admin_exists = 0 THEN
    INSERT INTO users (
      name, 
      password_hash, 
      can_see_contents,
      is_active,
      is_admin,
      created_at,
      updated_at
    ) VALUES (
      'admin',
      -- admin123 のハッシュ値
      '$2b$12$SWxPB7KBqvFrtsz1gT3jN.4YBLMg0c0APuNS8oVjDYEDYCHX8.9eq',
      TRUE,   -- コンテンツ閲覧権限
      TRUE,   -- アクティブユーザー
      TRUE,   -- 管理者権限
      NOW(),  -- 作成日時
      NOW()   -- 更新日時
    );
    RAISE NOTICE 'ユーザー "admin" を管理者権限で作成しました。パスワード: admin123';
  ELSE
    -- 既存のadminユーザーに管理者権限を付与
    UPDATE users 
    SET 
      is_admin = TRUE,
      can_see_contents = TRUE,
      is_active = TRUE,
      password_hash = '$2b$12$SWxPB7KBqvFrtsz1gT3jN.4YBLMg0c0APuNS8oVjDYEDYCHX8.9eq',
      updated_at = NOW()
    WHERE name = 'admin';
    RAISE NOTICE 'ユーザー "admin" に管理者権限を付与しました。パスワード: admin123';
  END IF;
END $$;

-- 管理者権限を持つユーザーを確認
SELECT id, name, is_admin, is_active, can_see_contents, created_at FROM users WHERE is_admin = TRUE;
