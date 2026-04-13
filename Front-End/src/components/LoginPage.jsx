// LoginPage is a separate component responsible for rendering the login screen.
// It receives one prop: onBack.
// onBack is a function passed in from the parent so this page can switch back to the home page.
export default function LoginPage({ onBack }) {
    return (
        // Outer wrapper for the whole login page.
        // min-h-screen makes the page at least the full height of the screen.
        // bg-slate-100 sets the background color.
        // text-slate-800 sets the default text color.
        <div className="min-h-screen bg-slate-100 text-slate-800">

            {/* 
               Main page layout container.
               mx-auto centers the container horizontally.
               flex makes the sidebar and main content sit side by side.
               max-w-7xl limits the overall width so the page does not stretch too far.
            */}
            <div className="mx-auto flex min-h-screen max-w-7xl">

                {/*
                  Sidebar area.
                  hidden means it is hidden on small screens.
                  lg:flex means it becomes visible and uses flex layout on large screens and up.
                  w-64 gives the sidebar a fixed width.
                */}
                <aside className="hidden w-64 flex-col border-r border-slate-200 bg-white lg:flex">

                    {/* Branding / logo section at the top of the sidebar */}
                    <div className="border-b border-slate-200 px-8 py-8">
                        <h1 className="text-3xl font-bold tracking-tight text-slate-900">PsNQs</h1>
                        <p className="mt-2 text-sm text-slate-500">Meeting Queue Manager</p>
                    </div>

                    {/* Navigation area inside the sidebar */}
                    <nav className="flex-1 px-4 py-6">
                        <div className="space-y-2">

                            {/*
                              Home button.
                              When clicked, it calls onBack.
                              onBack comes from the parent component and changes the page back to "home".
                            */}
                            <button
                                onClick={onBack}
                                className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm text-slate-600 hover:bg-slate-100"
                            >
                                <span className="text-base">🏠</span>
                                Home
                            </button>

                            {/*
                              Login button in the sidebar.
                              This one is styled as the active/current page.
                              It does not need an onClick here because the user is already on the login page.
                            */}
                            <button className="flex w-full items-center gap-3 rounded-2xl bg-blue-50 px-4 py-3 text-left text-sm font-medium text-blue-700">
                                <span className="text-base">🔐</span>
                                Log In
                            </button>
                        </div>
                    </nav>
                </aside>

                {/*
                  Main content area for the login card.
                  flex-1 makes it take the remaining width not used by the sidebar.
                  items-center and justify-center center the login box vertically and horizontally.
                */}
                <main className="flex flex-1 items-center justify-center p-6 md:p-10">

                    {/* Login form card */}
                    <div className="w-full max-w-md rounded-3xl bg-white p-8 shadow-sm">

                        {/* Heading section inside the card */}
                        <div className="mb-8 text-center">
                            <h2 className="text-3xl font-bold tracking-tight text-slate-900">Welcome Back</h2>
                            <p className="mt-2 text-sm text-slate-500">
                                Sign in to view your queue status, meetings, and profile.
                            </p>
                        </div>

                        {/*
                          Form element for login inputs.
                          Right now, this is only visual.
                          It does not yet have any state variables, submit handler, or backend connection.
                        */}
                        <form className="space-y-5">

                            {/* Email input group */}
                            <div>
                                <label className="mb-2 block text-sm font-medium text-slate-700">School Email</label>
                                <input
                                    type="email"
                                    placeholder="name@csu.fullerton.edu"
                                    className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                />
                            </div>

                            {/* Password input group */}
                            <div>
                                <label className="mb-2 block text-sm font-medium text-slate-700">Password</label>
                                <input
                                    type="password"
                                    placeholder="Enter your password"
                                    className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                />
                            </div>

                            {/*
                              Row containing the "Remember me" checkbox and the "Forgot password?" button.
                              justify-between places them on opposite sides of the row.
                            */}
                            <div className="flex items-center justify-between text-sm">
                                <label className="flex items-center gap-2 text-slate-600">
                                    <input type="checkbox" className="rounded" />
                                    Remember me
                                </label>

                                {/*
                                  type="button" is important here.
                                  Without it, a button inside a form defaults to type="submit".
                                  This button should not submit the form.
                                */}
                                <button type="button" className="font-medium text-blue-600 hover:text-blue-700">
                                    Forgot password?
                                </button>
                            </div>

                            {/*
                              Submit button for the login form.
                              type="submit" tells the browser this button submits the form.
                              Since no onSubmit handler exists yet, this is still just part of the UI.
                            */}
                            <button
                                type="submit"
                                className="w-full rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
                            >
                                Log In
                            </button>
                        </form>

                        {/*
                          Bottom text and back button.
                          Clicking "Return home" also calls onBack to switch pages.
                        */}
                        <div className="mt-6 text-center text-sm text-slate-500">
                            Need to go back?{" "}
                            <button onClick={onBack} className="font-medium text-blue-600 hover:text-blue-700">
                                Return home
                            </button>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}