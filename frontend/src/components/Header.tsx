import { Box, Heading } from "@chakra-ui/react";

export default function Header() {
  return (
    <Box as="header" padding="4" bg="blue.600" color="white">
      <Heading size="lg">Living Ice Sheet Temperature</Heading>
    </Box>
  );
}
