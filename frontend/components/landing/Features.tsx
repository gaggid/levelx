import { TrendingUp, Users, Lightbulb } from "lucide-react";

export default function Features() {
  return (
    <section className="py-24 px-4">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-4xl font-bold text-center mb-16">Features</h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="p-6 bg-slate-900 rounded-lg">
            <TrendingUp className="w-12 h-12 text-purple-400 mb-4" />
            <h3 className="text-xl font-bold mb-2">Growth Score</h3>
            <p className="text-slate-400">Track your growth</p>
          </div>
          <div className="p-6 bg-slate-900 rounded-lg">
            <Users className="w-12 h-12 text-blue-400 mb-4" />
            <h3 className="text-xl font-bold mb-2">Peer Matches</h3>
            <p className="text-slate-400">Find similar accounts</p>
          </div>
          <div className="p-6 bg-slate-900 rounded-lg">
            <Lightbulb className="w-12 h-12 text-green-400 mb-4" />
            <h3 className="text-xl font-bold mb-2">Insights</h3>
            <p className="text-slate-400">Actionable tips</p>
          </div>
        </div>
      </div>
    </section>
  );
}