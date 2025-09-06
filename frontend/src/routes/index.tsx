import React from 'react';
import { createBrowserRouter } from 'react-router-dom';
import { ProtectedRoute } from '../components/ProtectedRoute';
import Ranking from '../pages/Ranking';
import StoreDetail from '../pages/StoreDetail';
import NotAllowed from '../pages/NotAllowed';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <ProtectedRoute />,
    children: [
      { index: true, element: <Ranking /> },
      { path: 'stores/:id', element: <StoreDetail /> }
    ]
  },
  { path: '/denied', element: <NotAllowed /> }
]);