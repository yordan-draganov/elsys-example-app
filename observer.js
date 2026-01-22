class NewsAgency {
  constructor() {
    this.subscribers = [];
  }

  subscribe(observer) {
    this.subscribers.push(observer);
  }

  unsubscribe(observer) {
    this.subscribers = this.subscribers.filter(o => o !== observer);
  }

  notify(news) {
    this.subscribers.forEach(observer => observer.update(news));
  }
}

class NewsChannel {
  constructor(name) {
    this.name = name;
  }

  update(news) {
    console.log(`${this.name} received news: ${news}`);
  }
}

const agency = new NewsAgency();

const btv = new NewsChannel("bTV");
const nova = new NewsChannel("Nova");

agency.subscribe(btv);
agency.subscribe(nova);

agency.notify("Breaking news: Daily weather explained!");
