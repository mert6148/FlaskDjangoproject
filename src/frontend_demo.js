async function ping() {
  const res = await fetch('/api/ping');
  const data = await res.json();
  console.log('ping->', data);
}

ping();
