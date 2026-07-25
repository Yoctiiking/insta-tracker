const syncBtn = document.getElementById("sync-btn");
const statusEl = document.getElementById("status");
const searchInput = document.getElementById("search-input");
const tbody = document.getElementById("results-body");
const followersCountEl = document.getElementById("followers-count");
const followingCountEl = document.getElementById("following-count");

// Dernières données reçues de l'API, indépendamment de ce qui est filtré/affiché
let currentData = [];

// Silhouette générique utilisée si la photo ne charge pas
const FALLBACK_AVATAR =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
      <rect width="40" height="40" fill="#0C1614"/>
      <circle cx="20" cy="15" r="7" fill="#A9A190"/>
      <path d="M6 36c2-9 8-13 14-13s12 4 14 13" fill="#A9A190"/>
    </svg>
  `);

const EMPTY_ICON = `
  <svg class="empty-icon" width="30" height="30" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="20" cy="20" r="17" stroke="currentColor" stroke-width="1.5"/>
    <path d="M13 20h14M20 13v14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.5"/>
  </svg>`;

function emptyRow(message) {
  tbody.innerHTML = `<tr class="empty-row"><td colspan="4">${EMPTY_ICON}${message}</td></tr>`;
}

function renderRows(data) {
  if (data.length === 0) {
    emptyRow(
      currentData.length === 0
        ? "Tout le monde te rend la pareille. Rien à signaler."
        : "Aucun résultat pour cette recherche."
    );
    return;
  }
  tbody.innerHTML = "";
  data.forEach((rel) => {
    const tr = document.createElement("tr");
    const imgUrl = rel.profile_pic_url
      ? `/api/proxy-image?url=${encodeURIComponent(rel.profile_pic_url)}`
      : FALLBACK_AVATAR;
    tr.innerHTML = `
      <td>
        <a href="https://instagram.com/${rel.username}" target="_blank" rel="noopener noreferrer">
          <img class="avatar" src="${imgUrl}" alt="${rel.username}" onerror="this.onerror=null;this.src='${FALLBACK_AVATAR}';">
        </a>
      </td>
      <td><span class="username">@${rel.username}</span></td>
      <td><span class="fullname">${rel.full_name || ""}</span></td>
      <td><button class="unfollow" data-username="${rel.username}">Unfollow</button></td>
    `;
    tbody.appendChild(tr);
  });
}

// Recalcule l'affichage à partir de currentData + ce qui est tapé dans la recherche
function applyFilter() {
  const q = searchInput.value.trim().toLowerCase();
  const filtered = q
    ? currentData.filter(
        (rel) =>
          rel.username.toLowerCase().includes(q) ||
          (rel.full_name || "").toLowerCase().includes(q)
      )
    : currentData;
  renderRows(filtered);
}

function updateCounts(followers, following) {
  followersCountEl.textContent = followers ?? "—";
  followingCountEl.textContent = following ?? "—";
}

// Fait -1 sur le compteur "Abonnements" affiché, sans requête serveur
function decrementFollowingCount() {
  const current = parseInt(followingCountEl.textContent, 10);
  if (!Number.isNaN(current)) {
    followingCountEl.textContent = current - 1;
  }
}

async function loadLatestCounts() {
  try {
    const res = await fetch("/api/snapshots");
    if (!res.ok) return;
    const snapshots = await res.json();
    if (snapshots.length === 0) return;
    updateCounts(snapshots[0].followers_count, snapshots[0].following_count);
  } catch (e) {
    // Silencieux : les compteurs restent affichés à "—"
  }
}

async function loadNonMutual() {
  const res = await fetch("/api/non-mutual");
  if (!res.ok) {
    currentData = [];
    emptyRow('Le registre est vide. Lance l\'audit pour voir qui manque à l\'appel.');
    return;
  }
  currentData = await res.json();
  applyFilter();
}

async function syncNow() {
  statusEl.classList.remove("is-success", "is-error");
  statusEl.textContent = "Audit en cours (peut prendre 1-2 min)...";
  syncBtn.disabled = true;
  try {
    const res = await fetch("/api/sync", { method: "POST" });
    const data = await res.json();
    statusEl.textContent = `${data.non_mutual_count} comptes non réciproques`;
    statusEl.classList.add("is-success");
    updateCounts(data.followers_count, data.following_count);
    await loadNonMutual();
  } catch (e) {
    statusEl.textContent = "L'audit a échoué. Réessaie.";
    statusEl.classList.add("is-error");
  } finally {
    syncBtn.disabled = false;
  }
}

tbody.addEventListener("click", async (e) => {
  if (e.target.classList.contains("unfollow")) {
    const username = e.target.dataset.username;
    const row = e.target.closest("tr");
    e.target.disabled = true;
    e.target.textContent = "...";
    await fetch(`/api/unfollow/${username}`, { method: "POST" });
    decrementFollowingCount();
    currentData = currentData.filter((rel) => rel.username !== username);
    row.classList.add("leaving");
    row.addEventListener("animationend", () => {
      row.remove();
      if (!tbody.querySelector("tr")) {
        applyFilter();
      }
    }, { once: true });
  }
});

syncBtn.addEventListener("click", syncNow);
searchInput.addEventListener("input", applyFilter);
loadNonMutual();
loadLatestCounts();