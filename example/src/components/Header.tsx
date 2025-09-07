import { BarChart3, User } from 'lucide-react';
import { Button } from './ui/button';

interface HeaderProps {
  isLoggedIn: boolean;
  onLoginClick: () => void;
  onProfileClick: () => void;
}

export function Header({ isLoggedIn, onLoginClick, onProfileClick }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 w-full bg-gradient-to-r from-blue-100/80 to-sky-100/80 backdrop-blur-sm shadow-sm">
      <div className="px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-700" />
            <h1 className="text-xl text-blue-700">稼働.com</h1>
          </div>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={isLoggedIn ? onProfileClick : onLoginClick}
            className="p-2 text-blue-700 hover:bg-blue-50/50"
          >
            <User className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </header>
  );
}