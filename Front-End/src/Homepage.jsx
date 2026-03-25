export default function PsNQsHomepage() {

    // JavaScript array of objects
    // Each object represents one "office hours session"
    // Temporary data (later this will be connected to the backend)
    const officeHours = [
        {
            name: "Professor Jones",        // Name of the staff member
            role: "Professor",             // Role (Professor or TA)
            studentsWaiting: 4,            // Number of students in queue
            status: "Open",                // Status of session
            subtitle: "Office Hours"       // Extra description
        },
        {
            name: "TA Smith",
            role: "TA",
            studentsWaiting: 2,
            status: "Open",
            subtitle: "Lab Help"
        }
    ];

    // This is what React renders to the screen
    return (

        // Outer container (full screen height)
        <div className="min-h-screen bg-slate-100 text-slate-800">

            {/* Main layout container (centers content + flex layout) */}
            <div className="mx-auto flex min-h-screen max-w-7xl">

                {/* Sidebar (hidden on small screens, visible on large screens) */}
                <aside className="hidden w-64 flex-col border-r border-slate-200 bg-white lg:flex">

                    {/* Top logo section */}
                    <div className="border-b border-slate-200 px-8 py-8">
                        <h1 className="text-3xl font-bold tracking-tight text-slate-900">PsNQs</h1>
                        <p className="mt-2 text-sm text-slate-500">Meeting Queue Manager</p>
                    </div>

                    {/* Navigation buttons */}
                    <nav className="flex-1 px-4 py-6">
                        <div className="space-y-2">

                            {/* Homepage / current page*/}
                            <button className="flex w-full items-center gap-3 rounded-2xl bg-blue-50 px-4 py-3 text-left text-sm font-medium text-blue-700">
                                <span className="text-base">🗓️</span>
                                Home
                            </button>

                            {/* Office hours and Profile UI */}
                            <button className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm text-slate-600 hover:bg-slate-100">
                                <span className="text-base">⏰</span>
                                Office Hours
                            </button>

                            <button className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm text-slate-600 hover:bg-slate-100">
                                <span className="text-base">👤</span>
                                Profile
                            </button>
                        </div>
                    </nav>
                </aside>

                {/* Main content area */}
                <main className="flex-1 p-6 md:p-10">

                    {/* Header / Hero Section */}
                    <div className="mb-8 flex flex-col gap-4 rounded-3xl bg-white p-6 shadow-sm md:flex-row md:items-center md:justify-between">

                        {/* Text section */}
                        <div>
                            <h2 className="text-3xl font-bold tracking-tight text-slate-900">
                                Welcome to Ps & Qs
                            </h2>
                            <p className="mt-2 max-w-2xl text-sm text-slate-500 md:text-base">
                                Join office hours, view available staff, and keep track of your queue position in one place.
                            </p>
                        </div>

                        {/* Buttons (Login / Get Started) */}
                        <div className="flex gap-3">
                            <button className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50">
                                Log In
                            </button>
                            <button className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-blue-700">
                                Get Started
                            </button>
                        </div>
                    </div>

                    {/* Main content split into 2 columns */}
                    <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">

                        {/* LEFT SIDE (Office Hours List) */}
                        <div className="rounded-3xl bg-white p-6 shadow-sm">

                            {/* Section header */}
                            <div className="mb-5 flex items-center justify-between">
                                <div>
                                    <h3 className="text-xl font-semibold text-slate-900">Available Office Hours</h3>
                                    <p className="mt-1 text-sm text-slate-500">Browse open sessions and join the queue.</p>
                                </div>

                                <button className="rounded-2xl border border-slate-200 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">
                                    View All
                                </button>
                            </div>

                            {/* We are looping through officeHours array */}
                            <div className="space-y-4">

                                {officeHours.map((person) => (

                                    // Each "person" becomes one card in the list
                                    <div
                                        key={person.name} // React needs a unique key for lists
                                        className="rounded-3xl border border-slate-200 p-5 transition hover:shadow-md"
                                    >

                                        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

                                            {/* Left side (profile info) */}
                                            <div className="flex items-center gap-4">

                                                {/* Avatar */}
                                                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-200 text-xl">
                                                    👤
                                                </div>

                                                {/* Name + role */}
                                                <div>
                                                    <h4 className="text-lg font-semibold text-slate-900">
                                                        {person.name}
                                                    </h4>
                                                    <p className="text-sm text-slate-500">
                                                        {person.role} • {person.subtitle}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Right side (status + actions) */}
                                            <div className="flex flex-wrap items-center gap-3">

                                                {/* Status badge */}
                                                <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                                                    {person.status}
                                                </span>

                                                {/* Queue count */}
                                                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                                                    {person.studentsWaiting} waiting
                                                </span>

                                                {/* Join button */}
                                                <button className="rounded-2xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
                                                    Join Queue
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* RIGHT SIDE */}
                        <div className="space-y-6">

                            {/* How it works message */}
                            <section className="rounded-3xl bg-white p-6 shadow-sm">
                                <h3 className="text-xl font-semibold text-slate-900">How It Works</h3>

                                {/* Loop again (steps list) */}
                                <div className="mt-5 space-y-4">
                                    {[
                                        "Create or log into your account",
                                        "Choose an office hours session",
                                        "Join the queue and track your position",
                                        "Meet with your professor or TA"
                                    ].map((step, index) => (

                                        <div key={step} className="flex items-start gap-3">

                                            {/* Number circle */}
                                            <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white">
                                                {index + 1}
                                            </div>

                                            {/* Step text */}
                                            <p className="text-sm leading-6 text-slate-600">
                                                {step}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            </section>

                            {/* Info box */}
                            <section className="rounded-3xl bg-slate-900 p-6 text-white shadow-sm">
                                <h3 className="text-xl font-semibold">Why Ps & Qs?</h3>

                                <div className="mt-4 space-y-3 text-sm text-slate-300">
                                    <p>• Cleaner queue management for office hours</p>
                                    <p>• Easy student access to available meetings</p>
                                    <p>• Future support for grouping, scheduling, and notifications</p>
                                </div>
                            </section>
                        </div>
                    </section>
                </main>
            </div>
        </div>
    );
}