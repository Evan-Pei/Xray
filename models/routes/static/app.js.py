document.addEventListener("DOMContentLoaded", async () => {
  const form = document.getElementById("booking-form");
  const message = document.getElementById("form-message");
  const historyList = document.getElementById("history-list");
  const deleteButton = document.getElementById("delete-button");
  const resetButton = document.getElementById("reset-button");
  const machineSelect = document.getElementById("machine_id");
  const bookingIdField = document.getElementById("booking-id");
  const fields = {
    title: document.getElementById("title"),
    machine_id: machineSelect,
    start: document.getElementById("start"),
    end: document.getElementById("end"),
    purpose: document.getElementById("purpose"),
    status: document.getElementById("status"),
  };

  async function request(url, options = {}) {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.error || "Request failed");
    }
    return payload;
  }

  function setMessage(text, isError = false) {
    message.textContent = text;
    message.style.color = isError ? "#d64545" : "#0f4c81";
  }

  function toLocalInputValue(dateString) {
    const date = new Date(dateString);
    const offset = date.getTimezoneOffset();
    const local = new Date(date.getTime() + offset * 60000);
    return local.toISOString().slice(0, 16);
  }

  function resetForm() {
    bookingIdField.value = "";
    form.reset();
    deleteButton.disabled = true;
    historyList.innerHTML = "<li>選擇自己的申請以查看歷史。</li>";
    setMessage("");
  }

  async function loadMachines() {
    const machines = await request("/api/machines");
    machineSelect.innerHTML = machines
      .map(
        (machine) =>
          `<option value="${machine.id}">${machine.name}</option>`
      )
      .join("");
  }

  async function loadHistory(bookingId) {
    const history = await request(`/api/bookings/${bookingId}/history`);
    historyList.innerHTML = history
      .map(
        (entry) =>
          `<li><strong>${entry.action}</strong> · ${new Date(
            entry.changed_at
          ).toLocaleString()}<br>${entry.snapshot.machine_name} / ${
            entry.snapshot.status
          }</li>`
      )
      .join("");
  }

  function populateForm(event) {
    const data = event.extendedProps;
    bookingIdField.value = event.id;
    fields.title.value = event.title;
    fields.machine_id.value = data.machine_id;
    fields.start.value = toLocalInputValue(event.startStr);
    fields.end.value = toLocalInputValue(event.endStr);
    fields.purpose.value = data.purpose || "";
    fields.status.value = data.status || "pending";
    deleteButton.disabled = !data.can_edit;

    if (data.can_edit) {
      loadHistory(event.id).catch((error) => setMessage(error.message, true));
    } else {
      historyList.innerHTML = "<li>只能查看自己的申請修改歷史。</li>";
    }
  }

  await loadMachines();

  const calendar = new FullCalendar.Calendar(document.getElementById("calendar"), {
    initialView: "dayGridMonth",
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay",
    },
    selectable: true,
    nowIndicator: true,
    slotMinTime: "07:00:00",
    slotMaxTime: "22:00:00",
    events: async (fetchInfo, successCallback, failureCallback) => {
      try {
        const bookings = await request(
          `/api/bookings?start=${encodeURIComponent(fetchInfo.startStr)}&end=${encodeURIComponent(fetchInfo.endStr)}`
        );
        successCallback(
          bookings.map((booking) => ({
            id: booking.id,
            title: `${booking.title} (${booking.machine_name})`,
            start: booking.start,
            end: booking.end,
            backgroundColor: booking.status === "approved" ? "#2f9e44" : "#0f62fe",
            borderColor: booking.status === "cancelled" ? "#d64545" : undefined,
            extendedProps: booking,
          }))
        );
      } catch (error) {
        failureCallback(error);
        setMessage(error.message, true);
      }
    },
    select(selectionInfo) {
      bookingIdField.value = "";
      deleteButton.disabled = true;
      fields.start.value = toLocalInputValue(selectionInfo.startStr);
      fields.end.value = toLocalInputValue(selectionInfo.endStr);
      setMessage("已帶入所選時段，請完成申請資料。");
    },
    eventClick(info) {
      populateForm(info.event);
      setMessage(
        info.event.extendedProps.can_edit
          ? "您可以修改或刪除此申請。"
          : "此時段已被預約，僅可查看內容。"
      );
    },
  });

  calendar.render();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const bookingId = bookingIdField.value;
    const payload = {
      title: fields.title.value,
      machine_id: fields.machine_id.value,
      start: fields.start.value,
      end: fields.end.value,
      purpose: fields.purpose.value,
      status: fields.status.value,
    };

    try {
      await request(bookingId ? `/api/bookings/${bookingId}` : "/api/bookings", {
        method: bookingId ? "PUT" : "POST",
        body: JSON.stringify(payload),
      });
      setMessage(bookingId ? "申請已更新。" : "申請已建立。");
      resetForm();
      calendar.refetchEvents();
    } catch (error) {
      setMessage(error.message, true);
    }
  });

  deleteButton.addEventListener("click", async () => {
    const bookingId = bookingIdField.value;
    if (!bookingId) {
      return;
    }

    try {
      await request(`/api/bookings/${bookingId}`, { method: "DELETE" });
      setMessage("申請已刪除。");
      resetForm();
      calendar.refetchEvents();
    } catch (error) {
      setMessage(error.message, true);
    }
  });

  resetButton.addEventListener("click", resetForm);
});