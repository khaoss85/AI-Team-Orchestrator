'use client'

import React from 'react'
import { User, Settings, Bell, Shield, Palette } from 'lucide-react'

export default function ProfilePage() {
  return (
    <div className="container mx-auto py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Profile & Settings</h1>
          <p className="text-gray-600">
            Manage your account, preferences, and system settings
          </p>
        </div>

        {/* Settings Categories */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors cursor-pointer">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-blue-50 rounded-lg">
                <User className="w-5 h-5 text-blue-600" />
              </div>
              <h3 className="font-medium text-gray-900">Account Settings</h3>
            </div>
            <p className="text-sm text-gray-600">
              Update your profile information, email, and password
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors cursor-pointer">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-green-50 rounded-lg">
                <Bell className="w-5 h-5 text-green-600" />
              </div>
              <h3 className="font-medium text-gray-900">Notifications</h3>
            </div>
            <p className="text-sm text-gray-600">
              Configure how and when you receive notifications
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors cursor-pointer">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-purple-50 rounded-lg">
                <Palette className="w-5 h-5 text-purple-600" />
              </div>
              <h3 className="font-medium text-gray-900">Appearance</h3>
            </div>
            <p className="text-sm text-gray-600">
              Customize the interface theme and display preferences
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors cursor-pointer">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-red-50 rounded-lg">
                <Shield className="w-5 h-5 text-red-600" />
              </div>
              <h3 className="font-medium text-gray-900">Security</h3>
            </div>
            <p className="text-sm text-gray-600">
              Manage your security settings and API keys
            </p>
          </div>
        </div>

        {/* Quick Settings */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">Quick Settings</h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <h3 className="font-medium text-gray-900">Enable minimal sidebar</h3>
                <p className="text-sm text-gray-600">Use the new floating sidebar design</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between py-3 border-b border-gray-100">
              <div>
                <h3 className="font-medium text-gray-900">Real-time notifications</h3>
                <p className="text-sm text-gray-600">Get notified about task completions and updates</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between py-3">
              <div>
                <h3 className="font-medium text-gray-900">Show thinking processes</h3>
                <p className="text-sm text-gray-600">Display AI reasoning steps in conversations</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Migration Notice */}
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <div className="p-1 bg-yellow-100 rounded-full">
              <Settings className="w-4 h-4 text-yellow-600" />
            </div>
            <div>
              <h3 className="font-medium text-yellow-900 mb-1">Settings Migration</h3>
              <p className="text-sm text-yellow-700">
                We've moved user settings here for better organization. System-wide settings 
                are now managed per-project, while personal preferences remain in your profile.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}