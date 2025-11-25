import { Button } from "@/components/ui/button";

export default function Pricing() {
  return (
    <section className="py-24 px-4">
      <div className="max-w-6xl mx-auto text-center">
        <h2 className="text-4xl font-bold mb-16">Pricing</h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="p-8 bg-slate-900 rounded-lg border border-slate-800">
            <h3 className="text-2xl font-bold mb-4">Free</h3>
            <div className="text-4xl font-bold mb-4">$0</div>
            <Button className="w-full">Get Started</Button>
          </div>
          <div className="p-8 bg-slate-900 rounded-lg border-2 border-purple-500">
            <h3 className="text-2xl font-bold mb-4">Pro</h3>
            <div className="text-4xl font-bold mb-4">$29</div>
            <Button className="w-full btn-gradient">Upgrade</Button>
          </div>
          <div className="p-8 bg-slate-900 rounded-lg border border-slate-800">
            <h3 className="text-2xl font-bold mb-4">Enterprise</h3>
            <div className="text-4xl font-bold mb-4">$79</div>
            <Button className="w-full">Contact</Button>
          </div>
        </div>
      </div>
    </section>
  );
}