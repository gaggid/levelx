export default function HowItWorks() {
  return (
    <section className="py-24 px-4 bg-slate-900/30">
      <div className="max-w-6xl mx-auto text-center">
        <h2 className="text-4xl font-bold mb-16">How It Works</h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div>
            <div className="text-6xl font-bold text-purple-400 mb-4">1</div>
            <h3 className="text-xl font-bold mb-2">Connect</h3>
            <p className="text-slate-400">Link your X account</p>
          </div>
          <div>
            <div className="text-6xl font-bold text-purple-400 mb-4">2</div>
            <h3 className="text-xl font-bold mb-2">Analyze</h3>
            <p className="text-slate-400">AI studies your profile</p>
          </div>
          <div>
            <div className="text-6xl font-bold text-purple-400 mb-4">3</div>
            <h3 className="text-xl font-bold mb-2">Grow</h3>
            <p className="text-slate-400">Get actionable insights</p>
          </div>
        </div>
      </div>
    </section>
  );
}