interface PlaceholderPageProps { title: string; description: string; }
export function PlaceholderPage({ title, description }: PlaceholderPageProps) { return <section><p className="mb-2 text-sm font-medium text-primary">Portal</p><h2 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h2><p className="mt-2 text-sm text-slate-500">{description}</p></section>; }
