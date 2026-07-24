const syncBtn = document.getElementById("sync-btn");
const statusEl = document.getElementById("status");
const tbody = document.getElementById("results-body");

async function loadNonMutual() {
  const res = await fetch("/api/non-mutual");
  if (!res.ok) {
    tbody.innerHTML = `<tr><td colspan="3">Aucune donnée. Clique sur "Synchroniser".</td></tr>`;
    return;
  }
  const data = await res.json();
  tbody.innerHTML = "";
  data.forEach((rel) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>@${rel.username}</td>
      <td>${rel.full_name || ""}</td>
      <td><button class="unfollow" data-username="${rel.username}">Unfollow</button></td>
    `;
    tbody.appendChild(tr);
  });
}

async function syncNow() {
  statusEl.textContent = "Synchronisation en cours (peut prendre 1-2 min)...";
  syncBtn.disabled = true;
  try {
    const res = await fetch("/api/sync", { method: "POST" });
    const data = await res.json();
    statusEl.textContent = `${data.non_mutual_count} comptes non-mutuels trouvés.`;
    await loadNonMutual();
  } catch (e) {
    statusEl.textContent = "Erreur pendant la synchronisation.";
  } finally {
    syncBtn.disabled = false;
  }
}

tbody.addEventListener("click", async (e) => {
  if (e.target.classList.contains("unfollow")) {
    const username = e.target.dataset.username;
    e.target.disabled = true;
    e.target.textContent = "...";
    await fetch(`/api/unfollow/${username}`, { method: "POST" });
    e.target.closest("tr").remove();
  }
});

syncBtn.addEventListener("click", syncNow);
loadNonMutual();
