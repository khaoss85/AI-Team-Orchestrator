import Link from 'next/link';

export default function Home() {
  return (
    <div className="container mx-auto">
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h1 className="text-2xl font-semibold mb-4">Benvenuto in AI Team Orchestrator</h1>
        <p className="text-gray-600 mb-4">
          Gestisci team di agenti AI che lavorano in autonomia sui tuoi progetti.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-100">
            <h3 className="text-indigo-700 font-medium mb-2">Progetti Attivi</h3>
            <div className="text-3xl font-bold">3</div>
            <Link href="/projects" className="text-sm text-indigo-600 mt-2 inline-block">
              Visualizza progetti
            </Link>
          </div>
          
          <div className="bg-emerald-50 p-4 rounded-lg border border-emerald-100">
            <h3 className="text-emerald-700 font-medium mb-2">Agenti Attivi</h3>
            <div className="text-3xl font-bold">12</div>
            <Link href="/teams" className="text-sm text-emerald-600 mt-2 inline-block">
              Gestisci agenti
            </Link>
          </div>
          
          <div className="bg-amber-50 p-4 rounded-lg border border-amber-100">
            <h3 className="text-amber-700 font-medium mb-2">Attività Completate</h3>
            <div className="text-3xl font-bold">27</div>
            <Link href="/projects" className="text-sm text-amber-600 mt-2 inline-block">
              Visualizza attività
            </Link>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">Progetti Recenti</h2>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="border-b pb-3 last:border-0">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium">Progetto di esempio {i}</h3>
                    <p className="text-sm text-gray-500">3 agenti · 8 attività</p>
                  </div>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                    Attivo
                  </span>
                </div>
              </div>
            ))}
          </div>
          <Link href="/projects" className="text-sm text-indigo-600 mt-4 inline-block">
            Visualizza tutti
          </Link>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">Crea Nuovo Progetto</h2>
          <p className="text-gray-600 mb-4">
            Inizia un nuovo progetto e lascia che i nostri agenti AI lavorino per te.
          </p>
          <Link href="/projects/new" className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition">
            Nuovo Progetto
          </Link>
        </div>
      </div>
    </div>
  );
}