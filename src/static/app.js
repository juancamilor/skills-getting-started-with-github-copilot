document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Helper function to show messages
  function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");

    // Hide message after 5 seconds
    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  // Function to update a single activity card
  async function updateActivityCard(activityName) {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();
      
      if (!activities[activityName]) {
        console.error(`Activity ${activityName} not found`);
        return;
      }

      const details = activities[activityName];
      const existingCard = document.querySelector(`[data-activity-name="${activityName}"]`);
      
      if (!existingCard) {
        console.error(`Card for ${activityName} not found`);
        return;
      }

      const spotsLeft = details.max_participants - details.participants.length;

      // Update only the dynamic parts
      const availabilityParagraph = existingCard.querySelector('.availability');
      if (availabilityParagraph) {
        availabilityParagraph.innerHTML = '';
        const availabilityStrong = document.createElement("strong");
        availabilityStrong.textContent = "Availability:";
        availabilityParagraph.appendChild(availabilityStrong);
        availabilityParagraph.appendChild(document.createTextNode(` ${spotsLeft} spots left`));
      }

      // Update participants section
      const participantsSection = existingCard.querySelector('.participants-section');
      participantsSection.innerHTML = '';

      const participantsLabel = document.createElement("strong");
      participantsLabel.textContent = "Participants:";
      participantsSection.appendChild(participantsLabel);

      if (details.participants.length > 0) {
        const participantsList = document.createElement("ul");
        participantsList.className = "participants-list";

        details.participants.forEach(email => {
          const listItem = document.createElement("li");
          listItem.textContent = email;

          const deleteBtn = document.createElement("button");
          deleteBtn.className = "remove-participant-btn";
          deleteBtn.setAttribute("data-activity", activityName);
          deleteBtn.setAttribute("data-email", email);
          deleteBtn.setAttribute("aria-label", `Remove ${email} from ${activityName}`);
          deleteBtn.textContent = "🗑️";

          listItem.appendChild(deleteBtn);
          participantsList.appendChild(listItem);
        });

        participantsSection.appendChild(participantsList);
      } else {
        const noParticipants = document.createElement("p");
        noParticipants.className = "no-participants";
        noParticipants.textContent = "No participants yet. Be the first to sign up!";
        participantsSection.appendChild(noParticipants);
      }
    } catch (error) {
      console.error("Error updating activity card:", error);
      // Fallback to full refresh on error
      fetchActivities();
    }
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";
        activityCard.dataset.activityName = name;

        const spotsLeft = details.max_participants - details.participants.length;

        // Create activity card structure using DOM methods to prevent XSS
        const title = document.createElement("h4");
        title.textContent = name;

        const description = document.createElement("p");
        description.textContent = details.description;

        const schedule = document.createElement("p");
        const scheduleStrong = document.createElement("strong");
        scheduleStrong.textContent = "Schedule:";
        schedule.appendChild(scheduleStrong);
        schedule.appendChild(document.createTextNode(" " + details.schedule));

        const availability = document.createElement("p");
        availability.className = "availability";
        const availabilityStrong = document.createElement("strong");
        availabilityStrong.textContent = "Availability:";
        availability.appendChild(availabilityStrong);
        availability.appendChild(document.createTextNode(` ${spotsLeft} spots left`));

        const participantsSection = document.createElement("div");
        participantsSection.className = "participants-section";

        const participantsLabel = document.createElement("strong");
        participantsLabel.textContent = "Participants:";
        participantsSection.appendChild(participantsLabel);

        // Build participants list
        if (details.participants.length > 0) {
          const participantsList = document.createElement("ul");
          participantsList.className = "participants-list";

          details.participants.forEach(email => {
            const listItem = document.createElement("li");
            listItem.textContent = email;

            const deleteBtn = document.createElement("button");
            deleteBtn.className = "remove-participant-btn";
            deleteBtn.setAttribute("data-activity", name);
            deleteBtn.setAttribute("data-email", email);
            deleteBtn.setAttribute("aria-label", `Remove ${email} from ${name}`);
            deleteBtn.textContent = "🗑️";

            listItem.appendChild(deleteBtn);
            participantsList.appendChild(listItem);
          });

          participantsSection.appendChild(participantsList);
        } else {
          const noParticipants = document.createElement("p");
          noParticipants.className = "no-participants";
          noParticipants.textContent = "No participants yet. Be the first to sign up!";
          participantsSection.appendChild(noParticipants);
        }

        activityCard.appendChild(title);
        activityCard.appendChild(description);
        activityCard.appendChild(schedule);
        activityCard.appendChild(availability);
        activityCard.appendChild(participantsSection);

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
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
        showMessage(result.message, "success");
        signupForm.reset();
        // Update only the affected activity card instead of refreshing everything
        updateActivityCard(activity);
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  // Handle delete participant
  activitiesList.addEventListener("click", async (event) => {
    if (event.target.classList.contains("remove-participant-btn")) {
      const activity = event.target.dataset.activity;
      const email = event.target.dataset.email;

      const confirmationMessage = `Remove participant "${email}" from activity "${activity}"?`;
      if (!confirm(confirmationMessage)) {
        return;
      }

      try {
        const response = await fetch(
          `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
          {
            method: "DELETE",
          }
        );

        const result = await response.json();

        if (response.ok) {
          // Update only the affected activity card instead of refreshing everything
          updateActivityCard(activity);
          showMessage(result.message, "success");
        } else {
          showMessage(result.detail || "An error occurred", "error");
        }
      } catch (error) {
        showMessage("Failed to remove participant. Please try again.", "error");
        console.error("Error removing participant:", error);
      }
    }
  });

  // Initialize app
  fetchActivities();
});
