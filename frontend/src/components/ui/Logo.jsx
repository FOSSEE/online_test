import React from 'react';
import { Link } from 'react-router-dom';

const Logo = ({ size = 'md', showText = true }) => {
  const sizes = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
    xl: 'w-20 h-20'
  };

  const textSizes = {
    sm: 'text-lg',
    md: 'text-xl',
    lg: 'text-2xl',
    xl: 'text-3xl'
  };

  return (
    <Link to="/" className="flex items-center gap-3">
      <div className={`${sizes[size]} flex items-center justify-center rounded-full overflow-hidden`}>
        
        <img 
          src="/yaksh_circular_logo.png" 
          alt="Yaksh Logo" 
          className="w-full h-full object-contain"
        />
      </div>
      {showText && (
        <span className={`${textSizes[size]} font-bold`}>Yaksh</span>
      )}
    </Link>
  );
};

export default Logo;