import { useEffect, useState } from "react";

// ProfilePage displays the currently signed-in student's profile information.
// It supports two modes:
// 1. view mode
// 2. edit mode
//
// Props:
// currentStudent -> the currently authenticated student account
// onBack -> returns the user to the homepage
// onProfileUpdated -> sends the updated student object back to the parent
// onLogout -> logs the student out of the app
export default function ProfilePage({ currentStudent, onBack, onProfileUpdated, onLogout }) {
    /*
      profile stores the most recent student profile loaded from the backend.

      loading tracks whether the page is still loading the profile.

      message stores success/error feedback shown to the user.

      messageType helps style the feedback message differently depending on whether
      it is a success message or an error message.

      isEditing controls whether the page is in read-only mode or edit mode.

      formData stores the editable values when the user is changing their profile.
    */
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState("");
    const [messageType, setMessageType] = useState("success");
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState({
        cwid: "",
        first_name: "",
        middle_initial: "",
        last_name: "",
        school_email: "",
        contact_email: "",
        phone_number: "",
        dsl_status: false,
    });

    /*
      useEffect runs when the page first opens and whenever currentStudent changes.

      If no student is logged in, the page shows an error message.
      Otherwise, it fetches the student's saved profile from the backend.
    */
    useEffect(() => {
        async function loadProfile() {
            if (!currentStudent?.cwid) {
                setMessageType("error");
                setMessage("No student is currently signed in.");
                setLoading(false);
                return;
            }

            try {
                setLoading(true);
                setMessage("");

                const response = await fetch(
                    `http://127.0.0.1:5000/api/profile/${currentStudent.cwid}`
                );

                const rawText = await response.text();

                let data;
                try {
                    data = JSON.parse(rawText);
                } catch {
                    throw new Error("The profile response was not valid JSON.");
                }

                if (!response.ok) {
                    throw new Error(data.error || "Failed to load profile.");
                }

                setProfile(data);
                setFormData(data);
                setMessage("");
            } catch (err) {
                setMessageType("error");
                setMessage(err.message || "Something went wrong while loading the profile.");
            } finally {
                setLoading(false);
            }
        }

        loadProfile();
    }, [currentStudent]);

    /*
      handleInputChange updates one field inside formData whenever the user types.

      This keeps the form controlled by React state.
    */
    function handleInputChange(event) {
        const { name, value } = event.target;
        setFormData({
            ...formData,
            [name]: value,
        });
    }

    /*
      handleSaveProfile sends the updated editable profile fields to the backend.

      Before sending the request, this function performs a small amount of
      frontend validation so the user gets quicker feedback.

      If the update succeeds:
      - local profile state is refreshed
      - edit mode is turned off
      - the parent component is given the new student object
        so currentStudent stays in sync across the app
    */
    async function handleSaveProfile(event) {
        event.preventDefault();

        // Small frontend validation for required editable fields.
        if (formData.first_name.trim() === "") {
            setMessageType("error");
            setMessage("First name cannot be empty.");
            return;
        }

        if (formData.last_name.trim() === "") {
            setMessageType("error");
            setMessage("Last name cannot be empty.");
            return;
        }

        if (formData.contact_email.trim() === "") {
            setMessageType("error");
            setMessage("Contact email cannot be empty.");
            return;
        }

        try {
            setMessage("");

            const response = await fetch("http://127.0.0.1:5000/api/profile/update", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to update profile.");
            }

            setProfile(data.student);
            setFormData(data.student);
            setIsEditing(false);
            setMessageType("success");
            setMessage("Profile updated successfully.");

            // Send the updated student back to the parent so homepage/app state stays current.
            onProfileUpdated(data.student);
        } catch (err) {
            setMessageType("error");
            setMessage(err.message || "Something went wrong while updating the profile.");
        }
    }

    /*
      handleCancelEdit restores the form fields back to the last saved profile values
      and exits edit mode without saving changes.
    */
    function handleCancelEdit() {
        setFormData(profile);
        setIsEditing(false);
        setMessage("");
    }

    return (
        <div className="min-h-screen bg-slate-100 text-slate-800">
            <div className="mx-auto flex min-h-screen max-w-7xl">
                <aside className="hidden w-64 flex-col border-r border-slate-200 bg-white lg:flex">
                    <div className="border-b border-slate-200 px-8 py-8">
                        <h1 className="text-3xl font-bold tracking-tight text-slate-900">PsNQs</h1>
                        <p className="mt-2 text-sm text-slate-500">Meeting Queue Manager</p>
                    </div>

                    <nav className="flex-1 px-4 py-6">
                        <div className="space-y-2">
                            {/*
                              Home navigation button.
                              Clicking this button returns the user to the homepage.
                            */}
                            <button
                                onClick={onBack}
                                className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm text-slate-600 hover:bg-slate-100"
                            >
                                <span className="text-base">🏠</span>
                                Home
                            </button>

                            {/*
                              Profile button styled as the active/current page.
                            */}
                            <button className="flex w-full items-center gap-3 rounded-2xl bg-blue-50 px-4 py-3 text-left text-sm font-medium text-blue-700">
                                <span className="text-base">👤</span>
                                Profile
                            </button>

                            {/*
                              Log out button.
                              Clicking this clears the current student and returns them to the home page.
                            */}
                            <button
                                onClick={onLogout}
                                className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm text-slate-600 hover:bg-slate-100"
                            >
                                <span className="text-base">🚪</span>
                                Log Out
                            </button>
                        </div>
                    </nav>
                </aside>

                <main className="flex-1 p-6 md:p-10">
                    <div className="mb-8 flex flex-col gap-4 rounded-3xl bg-white p-6 shadow-sm md:flex-row md:items-center md:justify-between">
                        <div>
                            <h2 className="text-3xl font-bold tracking-tight text-slate-900">Your Profile</h2>
                            <p className="mt-2 max-w-2xl text-sm text-slate-500 md:text-base">
                                View your saved student information and update editable contact details.
                            </p>

                            {/*
                              If a student is signed in, show their name and CWID as a small identity summary.
                            */}
                            {profile && (
                                <p className="mt-3 text-sm text-slate-600">
                                    Signed in as{" "}
                                    <span className="font-medium text-slate-900">
                                        {profile.first_name} {profile.last_name}
                                    </span>{" "}
                                    ({profile.cwid})
                                </p>
                            )}
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={onBack}
                                className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                            >
                                Return Home
                            </button>

                            {!isEditing && profile && (
                                <button
                                    onClick={() => {
                                        setMessage("");
                                        setIsEditing(true);
                                    }}
                                    className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
                                >
                                    Edit Profile
                                </button>
                            )}
                        </div>
                    </div>

                    {message && (
                        <div
                            className={`mb-6 rounded-2xl px-4 py-3 text-sm ${messageType === "error"
                                ? "bg-red-50 text-red-700"
                                : "bg-blue-50 text-blue-700"
                                }`}
                        >
                            {message}
                        </div>
                    )}

                    {loading ? (
                        <p className="text-sm text-slate-500">Loading profile...</p>
                    ) : !profile ? (
                        <p className="text-sm text-slate-500">No profile data available.</p>
                    ) : isEditing ? (
                        <form onSubmit={handleSaveProfile} className="rounded-3xl bg-white p-6 shadow-sm">
                            <div className="grid gap-5 md:grid-cols-2">
                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">CWID</label>
                                    <input
                                        type="text"
                                        name="cwid"
                                        value={formData.cwid}
                                        disabled
                                        className="w-full rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm text-slate-500 outline-none"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">School Email</label>
                                    <input
                                        type="email"
                                        name="school_email"
                                        value={formData.school_email}
                                        disabled
                                        className="w-full rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm text-slate-500 outline-none"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">First Name</label>
                                    <input
                                        type="text"
                                        name="first_name"
                                        value={formData.first_name}
                                        onChange={handleInputChange}
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">Middle Initial</label>
                                    <input
                                        type="text"
                                        name="middle_initial"
                                        value={formData.middle_initial}
                                        onChange={handleInputChange}
                                        maxLength={1}
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">Last Name</label>
                                    <input
                                        type="text"
                                        name="last_name"
                                        value={formData.last_name}
                                        onChange={handleInputChange}
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">Contact Email</label>
                                    <input
                                        type="email"
                                        name="contact_email"
                                        value={formData.contact_email}
                                        onChange={handleInputChange}
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">Phone Number</label>
                                    <input
                                        type="text"
                                        name="phone_number"
                                        value={formData.phone_number}
                                        onChange={handleInputChange}
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">DSL Status</label>
                                    <input
                                        type="text"
                                        value={formData.dsl_status ? "Yes" : "No"}
                                        disabled
                                        className="w-full rounded-2xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm text-slate-500 outline-none"
                                    />
                                </div>
                            </div>

                            <div className="mt-6 flex gap-3">
                                <button
                                    type="submit"
                                    className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
                                >
                                    Save Changes
                                </button>

                                <button
                                    type="button"
                                    onClick={handleCancelEdit}
                                    className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    ) : (
                        <section className="rounded-3xl bg-white p-6 shadow-sm">
                            <div className="grid gap-5 text-sm text-slate-600 md:grid-cols-2">
                                <p><span className="font-medium text-slate-900">CWID:</span> {profile.cwid}</p>
                                <p><span className="font-medium text-slate-900">School Email:</span> {profile.school_email}</p>
                                <p><span className="font-medium text-slate-900">First Name:</span> {profile.first_name}</p>
                                <p><span className="font-medium text-slate-900">Middle Initial:</span> {profile.middle_initial || "—"}</p>
                                <p><span className="font-medium text-slate-900">Last Name:</span> {profile.last_name}</p>
                                <p><span className="font-medium text-slate-900">Contact Email:</span> {profile.contact_email}</p>
                                <p><span className="font-medium text-slate-900">Phone Number:</span> {profile.phone_number || "—"}</p>
                                <p><span className="font-medium text-slate-900">DSL Status:</span> {profile.dsl_status ? "Yes" : "No"}</p>
                            </div>
                        </section>
                    )}
                </main>
            </div>
        </div>
    );
}