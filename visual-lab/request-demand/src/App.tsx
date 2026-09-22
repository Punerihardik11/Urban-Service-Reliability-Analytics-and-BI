import "./App.css";

import { AgedBacklogBklit } from "./components/aged-backlog/AgedBacklogBklit";
import { agedBacklogData } from "@/data/agedBacklogData";

function App() {
  return (
    <main className="min-h-screen bg-[#F6F7F5] px-[24px] py-[32px]">
      <AgedBacklogBklit data={agedBacklogData} />
    </main>
  );
}

export default App;