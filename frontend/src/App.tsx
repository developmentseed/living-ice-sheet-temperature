import { Box } from "@chakra-ui/react";
import Header from "./components/Header";
import Map from "./components/Map";

function App() {
  return (
    <Box height="100vh" display="flex" flexDirection="column" overflow="hidden">
      <Header />
      <Map />
    </Box>
  );
}

export default App;
