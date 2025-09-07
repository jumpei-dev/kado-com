import { MessageCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

interface TwitterPost {
  id: string;
  content: string;
  timestamp: string;
}

interface FooterProps {
  twitterPosts: TwitterPost[];
}

export function Footer({ twitterPosts }: FooterProps) {
  const handleLineConsultation = () => {
    // LINEへのリンク処理
    window.open('https://line.me/ti/p/@example', '_blank');
  };

  const handleTwitterProfile = () => {
    // Twitterプロフィールへのリンク処理
    window.open('https://twitter.com/example', '_blank');
  };

  return (
    <footer className="bg-gradient-to-r from-blue-50/60 to-sky-50/60 border-t border-blue-100 mt-8">
      <div className="px-4 py-6 space-y-6">
        {/* Twitter Section */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg text-center">
              <button 
                onClick={handleTwitterProfile}
                className="text-blue-700 hover:text-blue-800 transition-colors"
              >
                @稼働_com 運営者
              </button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {twitterPosts.map((post) => (
              <div key={post.id} className="bg-gradient-to-r from-white to-blue-50/30 rounded-lg p-3 border border-blue-100">
                <p className="text-sm text-gray-800 mb-2">{post.content}</p>
                <p className="text-xs text-gray-500">{post.timestamp}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* LINE Consultation */}
        <div className="text-center">
          <h3 className="text-lg mb-4">お店選びでお悩みの方へ</h3>
          <Button
            onClick={handleLineConsultation}
            className="w-full bg-gradient-to-r from-blue-200 to-sky-200 hover:from-blue-300 hover:to-sky-300 text-blue-800 py-3 rounded-lg flex items-center justify-center gap-2 border-0 shadow-sm"
          >
            <MessageCircle className="w-5 h-5" />
            LINE で相談する
          </Button>
          <p className="text-xs text-gray-500 mt-2">
            稼働率以外の情報も含めて、最適なお店をご提案します
          </p>
        </div>

        {/* Copyright */}
        <div className="text-center text-xs text-gray-400 pt-4 border-t">
          <p>© 2024 稼働.com All Rights Reserved</p>
        </div>
      </div>
    </footer>
  );
}