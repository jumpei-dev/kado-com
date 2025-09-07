import { useState, useMemo } from 'react';
import { Header } from './components/Header';
import { FilterBar } from './components/FilterBar';
import { RankingCard } from './components/RankingCard';
import { ShopDetail } from './components/ShopDetail';
import { Footer } from './components/Footer';
import { LoginModal } from './components/LoginModal';
import { Pagination } from './components/Pagination';
import { mockBusinesses, mockTwitterPosts, BusinessData } from './data/mockData';

interface FilterState {
  area: string;
  businessType: string;
  spec: string;
  period: string;
}

type ViewMode = 'ranking' | 'detail';

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('ranking');
  const [selectedBusinessId, setSelectedBusinessId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState<FilterState>({
    area: '全国',
    businessType: '全業種',
    spec: 'すべて',
    period: '先週'
  });

  const itemsPerPage = 20;

  const filteredBusinesses = useMemo(() => {
    return mockBusinesses.filter(business => {
      const matchesArea = filters.area === '全国' || 
        (filters.area === '東日本' && ['北海道', '東北', '関東', '中部'].includes(business.area)) ||
        (filters.area === '西日本' && ['関西', '中国', '四国', '九州・沖縄'].includes(business.area)) ||
        filters.area === business.area;
      
      const matchesBusinessType = filters.businessType === '全業種' || 
        business.businessType === filters.businessType;
      
      const matchesSpec = filters.spec === 'すべて' || 
        (filters.spec === 'ハイスペ' && business.spec === 'ハイスペ') ||
        business.spec === filters.spec;
      
      return matchesArea && matchesBusinessType && matchesSpec;
    });
  }, [filters]);

  const sortedBusinesses = useMemo(() => {
    return [...filteredBusinesses].sort((a, b) => b.utilizationRate - a.utilizationRate);
  }, [filteredBusinesses]);

  const totalPages = Math.ceil(sortedBusinesses.length / itemsPerPage);
  const paginatedBusinesses = sortedBusinesses.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const selectedBusiness = selectedBusinessId ? 
    mockBusinesses.find(b => b.id === selectedBusinessId) : null;

  const handleLogin = (username: string, password: string) => {
    // Simple mock login - in real app, validate credentials
    if (username && password) {
      setIsLoggedIn(true);
      setShowLoginModal(false);
    }
  };

  const handleBusinessClick = (id: string) => {
    setSelectedBusinessId(id);
    setViewMode('detail');
  };

  const handleBackToRanking = () => {
    setViewMode('ranking');
    setSelectedBusinessId(null);
  };

  const handleApplyFilters = () => {
    setCurrentPage(1); // Reset to first page when filters change
  };

  if (viewMode === 'detail' && selectedBusiness) {
    return (
      <ShopDetail
        business={selectedBusiness}
        isLoggedIn={isLoggedIn}
        onBack={handleBackToRanking}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50/40 to-sky-50/40">
      <div className="max-w-[640px] mx-auto bg-white/95 shadow-sm min-h-screen">
        <Header
          isLoggedIn={isLoggedIn}
          onLoginClick={() => setShowLoginModal(true)}
          onProfileClick={() => {/* Handle profile */}}
        />

        <FilterBar
          filters={filters}
          onFiltersChange={setFilters}
          onApplyFilters={handleApplyFilters}
        />

        <main className="px-4 py-6">
        <div className="mb-6">
          <h2 className="text-2xl text-center mb-2">稼働率ランキング</h2>
          <p className="text-sm text-gray-600 text-center">
            {sortedBusinesses.length}件の���舗が見つかりました
          </p>
        </div>

        <div className="space-y-4">
          {paginatedBusinesses.map((business, index) => {
            const globalRank = (currentPage - 1) * itemsPerPage + index + 1;
            return (
              <RankingCard
                key={business.id}
                business={business}
                rank={globalRank}
                isLoggedIn={isLoggedIn}
                onClick={handleBusinessClick}
              />
            );
          })}
        </div>

        {paginatedBusinesses.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">
              検索条件に該当する店舗が見つかりませんでした。
            </p>
          </div>
        )}

        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      </main>

        <Footer twitterPosts={mockTwitterPosts} />

        <LoginModal
          isOpen={showLoginModal}
          onClose={() => setShowLoginModal(false)}
          onLogin={handleLogin}
        />
      </div>
    </div>
  );
}