import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useMe } from '../hooks/useMe';
import LoadingSpinner from './LoadingSpinner';

export const ProtectedRoute: React.FC = () => {
  const { data: user, isLoading, error } = useMe();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error || !user || !user.permissions?.length) {
    return <Navigate to="/denied" replace />;
  }

  return <Outlet />;
};
