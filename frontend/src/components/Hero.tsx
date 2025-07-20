import React from 'react';

const Hero: React.FC = () => {
  return (
    <div className="bg-gradient-to-b from-blue-50 to-white py-20">
      <div className="max-w-4xl mx-auto text-center px-4">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          🎙️ Podcast Digest
        </h1>
        <p className="text-2xl text-gray-600 mb-4">
          每周精选英文播客，中文摘要直达邮箱
        </p>
        <p className="text-lg text-gray-500 max-w-2xl mx-auto">
          我们精选最优质的英文播客内容，使用 AI 技术生成精准的中文摘要，
          让您轻松了解全球最新观点和洞察。
        </p>
      </div>
    </div>
  );
};

export default Hero;