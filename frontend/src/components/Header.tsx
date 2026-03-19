import { LuThermometerSnowflake } from "react-icons/lu";
import { Box, Button, HStack, Heading, Icon, Link } from "@chakra-ui/react";

export default function Header() {
  return (
    <HStack as="header" py="4" px="6" bg="blue.50" shadow="sm">
      <Heading size="lg">
        <HStack>
          <Icon>
            <LuThermometerSnowflake />
          </Icon>
          Living Ice Sheet Temperature
        </HStack>
      </Heading>
      <Box flex="1" />
      <Button variant={"surface"}>
        <a
          href="https://developmentseed.org/living-ice-sheet-temperature/docs/"
          target="_blank"
        >
          Docs
        </a>
      </Button>
    </HStack>
  );
}
