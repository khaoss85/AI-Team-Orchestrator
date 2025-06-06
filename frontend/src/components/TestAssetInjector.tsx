'use client';

import React, { useState } from 'react';

interface TestAssetInjectorProps {
  workspaceId: string;
  onClose: () => void;
}

const TestAssetInjector: React.FC<TestAssetInjectorProps> = ({ workspaceId, onClose }) => {
  const [injecting, setInjecting] = useState(false);

  const mockInstagramCalendar = {
    structured_content: {
      calendar_overview: {
        duration: "3 months",
        posting_frequency: "Daily posts + 3 reels per week",
        target_audience: "Male bodybuilding enthusiasts",
        growth_target: "200 followers per week",
        engagement_target: "+10% weekly increase"
      },
      monthly_breakdown: [
        {
          month: "Month 1 - Foundation Building",
          theme: "Establishing Authority & Community",
          post_count: 31,
          reel_count: 12,
          focus_areas: ["Form tutorials", "Beginner tips", "Motivation"]
        },
        {
          month: "Month 2 - Engagement Acceleration", 
          theme: "Interactive Content & Community Growth",
          post_count: 30,
          reel_count: 12,
          focus_areas: ["Q&A sessions", "Challenges", "Transformation stories"]
        },
        {
          month: "Month 3 - Authority & Monetization",
          theme: "Expert Positioning & Value Delivery",
          post_count: 31,
          reel_count: 12,
          focus_areas: ["Advanced techniques", "Nutrition deep-dives", "Program previews"]
        }
      ],
      sample_posts: [
        {
          date: "2024-12-20",
          type: "Carousel",
          title: "💪 5 ESERCIZI PER MASSA MUSCOLARE",
          caption: "Vuoi aumentare la massa muscolare? Ecco i 5 esercizi fondamentali che DEVI includere nella tua routine:\n\n1️⃣ SQUAT - Il re degli esercizi\n✅ 4 serie x 8-10 reps\n✅ Focus sulla tecnica perfetta\n\n2️⃣ PANCA PIANA - Petto esplosivo\n✅ 4 serie x 6-8 reps\n✅ Controllo nella fase negativa\n\n3️⃣ STACCHI - Potenza totale\n✅ 3 serie x 5-6 reps\n✅ Attivazione di tutto il corpo\n\n4️⃣ MILITARY PRESS - Spalle forti\n✅ 3 serie x 8-10 reps\n✅ Core sempre attivo\n\n5️⃣ TRAZIONI - Dorsali in crescita\n✅ 3 serie x max reps\n✅ Se non riesci, usa l'elastico\n\n💡 CONSIGLIO PRO: Progressione graduale sempre!\n\n🔥 Salva questo post per non perdere la tua scheda!\n\n#bodybuilding #palestra #massa #workout #motivazione #MyGyM #fitness #allenamento #muscoli #forza",
          hashtags: ["#bodybuilding", "#palestra", "#massa", "#workout", "#motivazione", "#MyGyM", "#fitness", "#allenamento"],
          engagement_strategy: "Ask followers to comment their current max reps",
          best_posting_time: "18:00"
        },
        {
          date: "2024-12-21", 
          type: "Reel",
          title: "MORNING WORKOUT ROUTINE ☀️",
          caption: "La mia routine mattutina per iniziare la giornata con energia:\n\n6:00 - Sveglia + acqua e limone\n6:15 - 10 min di stretching\n6:30 - Pre-workout naturale\n7:00 - Allenamento intenso\n8:30 - Colazione proteica\n\n💪 Chi si allena al mattino con me?\n\nTag un amico che ha bisogno di motivazione! 👇\n\n#morningworkout #routine #motivazione #MyGyM #fitness #lifestyle",
          hashtags: ["#morningworkout", "#routine", "#motivazione", "#MyGyM", "#fitness"],
          engagement_strategy: "Challenge followers to try morning routine",
          best_posting_time: "07:00"
        },
        {
          date: "2024-12-22",
          type: "Photo",
          title: "MEAL PREP SUNDAY 🥗",
          caption: "Preparazione pasti per la settimana:\n\n🍗 Pollo grigliato (2kg)\n🍚 Riso integrale (1,5kg)\n🥦 Verdure miste (1kg)\n🥚 Uova sode (12 pezzi)\n🥜 Noci e mandorle\n\n⏰ 2 ore di prep = 7 giorni di alimentazione perfetta\n\n💡 Il segreto? Preparare tutto in una volta!\n\n👆 Swipe per vedere i contenitori pronti\n\n📱 Vuoi la mia app per il meal prep? Link in bio!\n\n#mealprep #nutrition #bodybuilding #MyGyM #preparazione #alimentazione #domenica",
          hashtags: ["#mealprep", "#nutrition", "#bodybuilding", "#MyGyM", "#preparazione"],
          engagement_strategy: "Share meal prep tips in comments",
          best_posting_time: "12:00"
        }
      ],
      content_pillars: [
        {
          pillar: "Educational Content (40%)",
          description: "Form tutorials, exercise breakdowns, anatomy education",
          examples: ["Exercise technique videos", "Muscle anatomy explanations", "Common mistakes to avoid"]
        },
        {
          pillar: "Motivational Content (30%)",
          description: "Success stories, daily motivation, mindset tips",
          examples: ["Transformation Tuesday", "Monday motivation", "Mindset quotes"]
        },
        {
          pillar: "Lifestyle Content (20%)",
          description: "Day in the life, gym culture, personal stories",
          examples: ["Morning routines", "Gym day vlogs", "Behind the scenes"]
        },
        {
          pillar: "Nutritional Content (10%)",
          description: "Meal prep, supplements, dietary advice",
          examples: ["Meal prep Sunday", "Supplement guides", "Nutrition myths"]
        }
      ],
      engagement_metrics: {
        target_reach: "50,000 accounts per week",
        target_engagement_rate: "8-12%",
        target_saves: "500+ per post",
        target_shares: "100+ per post",
        growth_projection: "200 new followers weekly"
      }
    },
    rendered_html: `
      <div class="instagram-calendar max-w-4xl mx-auto p-6 bg-white">
        <div class="header bg-gradient-to-r from-purple-600 to-pink-600 text-white p-6 rounded-lg mb-6">
          <h1 class="text-3xl font-bold mb-2">📅 3-Month Instagram Editorial Calendar</h1>
          <p class="text-lg opacity-90">MyGyM - Male Bodybuilding Community Growth Strategy</p>
          <div class="flex flex-wrap gap-4 mt-4 text-sm">
            <div class="bg-white/20 px-3 py-1 rounded">🎯 Target: +200 followers/week</div>
            <div class="bg-white/20 px-3 py-1 rounded">📈 Engagement: +10% weekly</div>
            <div class="bg-white/20 px-3 py-1 rounded">⏰ Duration: 3 months</div>
          </div>
        </div>

        <div class="monthly-overview grid md:grid-cols-3 gap-4 mb-8">
          <div class="month-card bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 class="text-lg font-bold text-blue-800 mb-2">Month 1: Foundation</h3>
            <p class="text-blue-700 text-sm mb-3">Establishing Authority & Community</p>
            <div class="stats text-xs">
              <div>📝 31 posts | 🎬 12 reels</div>
              <div class="mt-1 text-blue-600">Form tutorials • Beginner tips • Motivation</div>
            </div>
          </div>
          
          <div class="month-card bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 class="text-lg font-bold text-green-800 mb-2">Month 2: Acceleration</h3>
            <p class="text-green-700 text-sm mb-3">Interactive Content & Growth</p>
            <div class="stats text-xs">
              <div>📝 30 posts | 🎬 12 reels</div>
              <div class="mt-1 text-green-600">Q&A sessions • Challenges • Stories</div>
            </div>
          </div>
          
          <div class="month-card bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h3 class="text-lg font-bold text-purple-800 mb-2">Month 3: Authority</h3>
            <p class="text-purple-700 text-sm mb-3">Expert Positioning & Value</p>
            <div class="stats text-xs">
              <div>📝 31 posts | 🎬 12 reels</div>
              <div class="mt-1 text-purple-600">Advanced techniques • Nutrition • Programs</div>
            </div>
          </div>
        </div>

        <div class="sample-posts mb-8">
          <h2 class="text-2xl font-bold text-gray-800 mb-4">📱 Sample Content Posts</h2>
          <div class="space-y-4">
            <div class="post-card bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-lg p-4">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center space-x-2">
                  <span class="text-lg">💪</span>
                  <h3 class="font-bold text-gray-800">5 ESERCIZI PER MASSA MUSCOLARE</h3>
                </div>
                <div class="text-xs text-gray-500">Dec 20 • Carousel</div>
              </div>
              <p class="text-sm text-gray-700 mb-3">
                Vuoi aumentare la massa muscolare? Ecco i 5 esercizi fondamentali: Squat, Panca Piana, Stacchi, Military Press, Trazioni con progressioni specifiche e consigli tecnici...
              </p>
              <div class="hashtags text-xs text-blue-600 mb-2">
                #bodybuilding #palestra #massa #workout #motivazione #MyGyM
              </div>
              <div class="engagement text-xs text-green-600">
                🎯 Strategy: Ask followers to comment their current max reps
              </div>
            </div>

            <div class="post-card bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center space-x-2">
                  <span class="text-lg">☀️</span>
                  <h3 class="font-bold text-gray-800">MORNING WORKOUT ROUTINE</h3>
                </div>
                <div class="text-xs text-gray-500">Dec 21 • Reel</div>
              </div>
              <p class="text-sm text-gray-700 mb-3">
                La routine mattutina completa: sveglia, stretching, pre-workout, allenamento intenso, colazione proteica. Timeline dettagliata per iniziare la giornata con energia...
              </p>
              <div class="hashtags text-xs text-blue-600 mb-2">
                #morningworkout #routine #motivazione #MyGyM #fitness
              </div>
              <div class="engagement text-xs text-green-600">
                🎯 Strategy: Challenge followers to try morning routine
              </div>
            </div>

            <div class="post-card bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-4">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center space-x-2">
                  <span class="text-lg">🥗</span>
                  <h3 class="font-bold text-gray-800">MEAL PREP SUNDAY</h3>
                </div>
                <div class="text-xs text-gray-500">Dec 22 • Photo</div>
              </div>
              <p class="text-sm text-gray-700 mb-3">
                Preparazione settimanale: 2kg pollo, 1.5kg riso integrale, verdure miste, uova sode. 2 ore di prep per 7 giorni di alimentazione perfetta...
              </p>
              <div class="hashtags text-xs text-blue-600 mb-2">
                #mealprep #nutrition #bodybuilding #MyGyM #preparazione
              </div>
              <div class="engagement text-xs text-green-600">
                🎯 Strategy: Share meal prep tips in comments
              </div>
            </div>
          </div>
        </div>

        <div class="content-strategy mb-8">
          <h2 class="text-2xl font-bold text-gray-800 mb-4">📊 Content Strategy Breakdown</h2>
          <div class="grid md:grid-cols-2 gap-4">
            <div class="strategy-card bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 class="font-bold text-yellow-800 mb-2">📚 Educational (40%)</h3>
              <p class="text-sm text-yellow-700">Form tutorials, exercise breakdowns, anatomy education</p>
            </div>
            <div class="strategy-card bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 class="font-bold text-red-800 mb-2">🔥 Motivational (30%)</h3>
              <p class="text-sm text-red-700">Success stories, daily motivation, mindset tips</p>
            </div>
            <div class="strategy-card bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h3 class="font-bold text-purple-800 mb-2">🏃 Lifestyle (20%)</h3>
              <p class="text-sm text-purple-700">Day in the life, gym culture, personal stories</p>
            </div>
            <div class="strategy-card bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 class="font-bold text-green-800 mb-2">🥘 Nutritional (10%)</h3>
              <p class="text-sm text-green-700">Meal prep, supplements, dietary advice</p>
            </div>
          </div>
        </div>

        <div class="metrics bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h2 class="text-2xl font-bold text-gray-800 mb-4">📈 Expected Performance Metrics</h2>
          <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="metric text-center">
              <div class="text-2xl font-bold text-blue-600">50K</div>
              <div class="text-sm text-gray-600">Weekly Reach</div>
            </div>
            <div class="metric text-center">
              <div class="text-2xl font-bold text-green-600">10%</div>
              <div class="text-sm text-gray-600">Engagement Rate</div>
            </div>
            <div class="metric text-center">
              <div class="text-2xl font-bold text-purple-600">500+</div>
              <div class="text-sm text-gray-600">Saves per Post</div>
            </div>
            <div class="metric text-center">
              <div class="text-2xl font-bold text-orange-600">200</div>
              <div class="text-sm text-gray-600">New Followers/Week</div>
            </div>
          </div>
        </div>
      </div>
    `,
    visual_summary: "Complete 3-month Instagram editorial calendar with specific posts, real captions, hashtags, and engagement strategies for MyGyM bodybuilding community growth",
    actionable_insights: [
      "92 total posts planned with specific dates and content",
      "36 reels strategically distributed across 3 months", 
      "Content pillars balanced for education, motivation, lifestyle, and nutrition",
      "Each post includes caption, hashtags, and engagement strategy",
      "Clear posting schedule optimized for target audience engagement times"
    ]
  };

  const injectTestAsset = async () => {
    setInjecting(true);
    try {
      // Simulate injection by storing in localStorage for the asset viewer
      localStorage.setItem('test_instagram_calendar', JSON.stringify(mockInstagramCalendar));
      
      alert('✅ Test asset injected! Now try clicking on "Enhanced Content Calendar" and you should see the detailed calendar with specific posts.');
      onClose();
    } catch (error) {
      console.error('Error injecting test asset:', error);
      alert('❌ Error injecting test asset');
    } finally {
      setInjecting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full">
        <div className="bg-blue-600 text-white p-4 rounded-t-lg">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">🧪 Test Asset Injector</h2>
            <button onClick={onClose} className="text-white hover:bg-blue-700 px-2 py-1 rounded">✕</button>
          </div>
        </div>
        
        <div className="p-6">
          <div className="mb-4">
            <h3 className="font-bold text-gray-800 mb-2">What this does:</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Injects a test Instagram calendar with REAL content</li>
              <li>• Includes specific posts with dates, captions, hashtags</li>
              <li>• Shows how the dual output format should look</li>
              <li>• Demonstrates the proper HTML rendering</li>
            </ul>
          </div>

          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h4 className="font-medium text-yellow-800 mb-1">📋 Expected Result:</h4>
            <p className="text-sm text-yellow-700">
              After injection, when you click "Enhanced Content Calendar" → "Visualizza", 
              you should see a beautiful calendar with specific posts instead of generic templates.
            </p>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={injectTestAsset}
              disabled={injecting}
              className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {injecting ? 'Injecting...' : '🚀 Inject Test Calendar'}
            </button>
            <button
              onClick={onClose}
              className="flex-1 bg-gray-100 text-gray-700 py-3 px-4 rounded-lg hover:bg-gray-200"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestAssetInjector;