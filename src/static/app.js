document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message and activity select
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      const template = document.getElementById("activity-template");

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const spotsLeft = details.max_participants - details.participants.length;

        if (template) {
          const clone = document.importNode(template.content, true);

          clone.querySelector(".activity-title").textContent = name;
          clone.querySelector(".activity-desc").textContent = details.description;
          clone.querySelector(".activity-schedule").textContent = details.schedule;
          clone.querySelector(".activity-availability").textContent = `${spotsLeft} spots left`;
          clone.querySelector(".participants-header .count").textContent = details.participants.length;

          const list = clone.querySelector(".participants");
          list.innerHTML = "";

          if (details.participants.length > 0) {
            details.participants.forEach((p) => {
              const li = document.createElement("li");
              li.className = "participant";

              const avatar = document.createElement("span");
              avatar.className = "avatar";
              avatar.textContent = getInitials(p);

              const nameSpan = document.createElement("span");
              nameSpan.className = "participant-name";
              nameSpan.textContent = p;

              li.appendChild(avatar);
              li.appendChild(nameSpan);
              list.appendChild(li);
            });
            clone.querySelector(".participants-empty").classList.add("hidden");
          } else {
            clone.querySelector(".participants-empty").classList.remove("hidden");
          }

          activitiesList.appendChild(clone);
        } else {
          // Header / basic info
          const title = document.createElement("h4");
          title.textContent = name;

          const desc = document.createElement("p");
          desc.textContent = details.description;

          const schedule = document.createElement("p");
          schedule.innerHTML = `<strong>Schedule:</strong> `;
          const scheduleText = document.createElement("span");
          scheduleText.textContent = details.schedule;
          schedule.appendChild(scheduleText);

          const avail = document.createElement("p");
          avail.innerHTML = `<strong>Availability:</strong> `;
          const availText = document.createElement("span");
          availText.textContent = `${spotsLeft} spots left`;
          avail.appendChild(availText);

          activitiesList.appendChild(title);
          activitiesList.appendChild(desc);
          activitiesList.appendChild(schedule);
          activitiesList.appendChild(avail);

          // Participants section
          const participantsSection = document.createElement("div");
          participantsSection.className = "participants-section";

          const participantsHeader = document.createElement("div");
          participantsHeader.className = "participants-header";
          const headerTitle = document.createElement("h5");
          headerTitle.textContent = "Participants ";
          const count = document.createElement("span");
          count.className = "count";
          count.textContent = details.participants.length;
          headerTitle.appendChild(count);
          participantsHeader.appendChild(headerTitle);
          participantsSection.appendChild(participantsHeader);

          const list = document.createElement("ul");
          list.className = "participants";

          if (details.participants.length > 0) {
            details.participants.forEach((p) => {
              const li = document.createElement("li");
              li.className = "participant";

              const avatar = document.createElement("span");
              avatar.className = "avatar";
              avatar.textContent = getInitials(p);

              const nameSpan = document.createElement("span");
              nameSpan.className = "participant-name";
              nameSpan.textContent = p;

              li.appendChild(avatar);
              li.appendChild(nameSpan);
              list.appendChild(li);
            });
          }

          participantsSection.appendChild(list);

          const emptyMsg = document.createElement("p");
          emptyMsg.className = "participants-empty";
          if (details.participants.length === 0) {
            emptyMsg.textContent = "No participants yet.";
          } else {
            emptyMsg.classList.add("hidden");
          }
          participantsSection.appendChild(emptyMsg);

          activitiesList.appendChild(participantsSection);

          // Add option to select dropdown
          const option = document.createElement("option");
          option.value = name;
          option.textContent = name;
          activitySelect.appendChild(option);
        }
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Helper: get initials for avatar from a name/email
  function getInitials(text) {
    if (!text) return "?";
    const parts = String(text).split(/[\s@._-]+/).filter(Boolean);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "message success";
        signupForm.reset();
        // Refresh activities so new participant appears immediately
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "message error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "message error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
