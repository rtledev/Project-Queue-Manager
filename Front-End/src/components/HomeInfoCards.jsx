// HomeInfoCards renders the informational cards on the right side of the homepage.
// These are currently static UI sections and do not require any props.
export default function HomeInfoCards() {
    return (
        <>
            {/* "How It Works" card */}
            <section className="rounded-3xl bg-white p-6 shadow-sm">
                <h3 className="text-xl font-semibold text-slate-900">How It Works</h3>

                <div className="mt-5 space-y-4">
                    {[
                        "Create or log into your account",
                        "Choose an office hours session",
                        "Join the queue and track your position",
                        "Meet with your professor or TA",
                    ].map((step, index) => (
                        <div key={step} className="flex items-start gap-3">
                            <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white">
                                {index + 1}
                            </div>

                            <p className="text-sm leading-6 text-slate-600">{step}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* "Why Ps & Qs?" card */}
            <section className="rounded-3xl bg-slate-900 p-6 text-white shadow-sm">
                <h3 className="text-xl font-semibold">Why Ps &amp; Qs?</h3>

                <div className="mt-4 space-y-3 text-sm text-slate-300">
                    <p>• Cleaner queue management for office hours</p>
                    <p>• Easy student access to available meetings</p>
                    <p>• Future support for grouping, scheduling, and notifications</p>
                </div>
            </section>
        </>
    );
}