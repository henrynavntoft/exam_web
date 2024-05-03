function test(items) {
  // console.log(items)
  items = JSON.parse(items);
  console.log(items);
  items.forEach((item) => {
    let marker = new mapboxgl.Marker()
      .setLngLat([item.item_lon, item.item_lat]) // Marker 1 coordinates
      .addTo(map);
  });
}
