import React, { useState } from 'react';
import { api, SubscribeRequest, SubscribeResponse } from '../services/api';

const SubscribeSection: React.FC = () => {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    setMessage('');
    
    try {
      const subscribeData: SubscribeRequest = {
        email: email.trim(),
        name: name.trim() || undefined,
        utm_source: 'website',
        utm_medium: 'organic'
      };
      
      const response: SubscribeResponse = await api.subscribeToNewsletter(subscribeData);
      
      if (response.success) {
        setStatus('success');
        setMessage(response.message);
        setEmail('');
        setName('');
      } else {
        setStatus('error');
        setMessage('訂閱失敗，請稍後再試。');
      }
    } catch (error: any) {
      setStatus('error');
      
      if (error.response?.status === 400) {
        setMessage(error.response.data.detail || '請檢查您的郵箱地址是否正確。');
      } else if (error.response?.status === 429) {
        setMessage('請求過於頻繁，請稍後再試。');
      } else if (error.response?.status >= 500) {
        setMessage('服務暫時不可用，請稍後再試。');
      } else {
        setMessage('網絡錯誤，請檢查您的網絡連接。');
      }
    }
  };

  return (
    <div className="py-20 bg-white">
      <div className="max-w-4xl mx-auto text-center px-4">
        <h2 className="text-3xl font-bold text-gray-900 mb-6">
          订阅每周播客摘要
        </h2>
        <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
          每周日收到精选播客的中文摘要，让您在短时间内了解最有价值的内容。
          完全免费，随时可以取消订阅。
        </p>
        
        <div className="max-w-md mx-auto">
          {status === 'success' ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="text-green-800">
                <h3 className="font-semibold mb-2">订阅成功！🎉</h3>
                <p className="text-sm">
                  {message || '请查看您的邮箱确认订阅。您将在每周日收到播客摘要。'}
                </p>
              </div>
            </div>
          ) : status === 'error' ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-4">
              <div className="text-red-800">
                <h3 className="font-semibold mb-2">订阅失败</h3>
                <p className="text-sm">{message}</p>
              </div>
            </div>
          ) : null}
          
          {status !== 'success' && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="您的姓名（可选）"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
                />
              </div>
              <div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="输入您的邮箱地址"
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
                />
              </div>
              <button
                type="submit"
                disabled={status === 'loading'}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors text-lg"
              >
                {status === 'loading' ? '订阅中...' : '免费订阅'}
              </button>
            </form>
          )}
          
          <p className="text-sm text-gray-500 mt-4">
            我们尊重您的隐私，不会向第三方分享您的邮箱地址。
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
          <div className="text-center">
            <div className="text-3xl mb-4">🤖</div>
            <h3 className="font-semibold text-gray-900 mb-2">AI 智能摘要</h3>
            <p className="text-gray-600 text-sm">
              使用先进的 AI 技术，提取播客核心内容
            </p>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-4">📅</div>
            <h3 className="font-semibold text-gray-900 mb-2">每周更新</h3>
            <p className="text-gray-600 text-sm">
              每周日准时发送，不错过任何精彩内容
            </p>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-4">🌏</div>
            <h3 className="font-semibold text-gray-900 mb-2">中英对照</h3>
            <p className="text-gray-600 text-sm">
              提供优质中文翻译，理解更加轻松
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubscribeSection;