// frontend/src/components/teacher/QuestionActionButtons.jsx (Update)
import React from 'react';
import { Link } from 'react-router-dom';
import { FaBook, FaUpload, FaPlus, FaRegQuestionCircle } from 'react-icons/fa';
import { FaPersonCircleQuestion } from "react-icons/fa6";

const QuestionActionButtons = ({ activeButton = null, onAddClick }) => {
  const buttons = [
    {
      label: 'Questions',
      shortLabel: 'Questions',
      path: '/teacher/questions',
      type: 'library',
      icon: <FaPersonCircleQuestion className="w-4 h-4" />,
    },
    {
      label: 'Upload Questions',
      shortLabel: 'Upload',
      path: '/teacher/upload-question',
      type: 'upload',
      icon: <FaUpload className="w-4 h-4" />,
    },
    
  ];

  return (
    <div className="mb-6 lg:mb-8">
      <div className="flex justify-center sm:justify-start gap-2 sm:gap-3 overflow-x-auto scrollbar-hide pb-1">
        {buttons.map((button) => {
          const isActive = activeButton === button.type;
          
          // Style classes (keep your existing classes)
          const btnClasses = `group relative px-4 sm:px-6 py-3 rounded-xl font-semibold transition-all duration-300 text-sm flex items-center gap-2.5 whitespace-nowrap flex-shrink-0 border-2 ${isActive
                ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-xl shadow-blue-600/30 hover:shadow-2xl hover:shadow-blue-600/40 border-transparent scale-101'
                : 'card-strong border-[var(--border-strong)] text-[var(--text-secondary)] hover:border-blue-500/40 hover:bg-blue-500/5 hover:text-blue-400 hover:shadow-md'
                }`;

          const content = (
            <>
              <span className={`transition-transform duration-300 ${isActive ? 'text-white' : 'text-blue-400 group-hover:scale-110'}`}>
                {button.icon}
              </span>
              <span className="hidden md:inline">{button.label}</span>
              <span className="md:hidden">{button.shortLabel}</span>
            </>
          );

          // If this is the "Add Question" button, render a <button> instead of a <Link>
          

          // Otherwise, render a <Link>
          return (
            <Link key={button.type} to={button.path} className={btnClasses}>
              {content}
              {isActive && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-[var(--bg-primary)] animate-pulse"></span>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
};

export default QuestionActionButtons;